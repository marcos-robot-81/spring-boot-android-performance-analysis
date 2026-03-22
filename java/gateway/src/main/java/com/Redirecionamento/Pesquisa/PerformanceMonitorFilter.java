package com.Redirecionamento.Pesquisa;

import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import org.springframework.web.server.WebFilter;
import org.springframework.web.server.WebFilterChain;
import org.springframework.http.client.reactive.ReactorClientHttpConnector;
import reactor.netty.http.client.HttpClient;
import reactor.netty.resources.ConnectionProvider;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.beans.factory.DisposableBean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.Redirecionamento.Pesquisa.tapyofdeta.Dados;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.lang.management.ManagementFactory;
import com.sun.management.OperatingSystemMXBean;
import java.time.Duration;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Locale;
import java.time.LocalDateTime;


@Component
public class PerformanceMonitorFilter implements WebFilter, DisposableBean {

    private static final Logger logger = LoggerFactory.getLogger(PerformanceMonitorFilter.class);
    private final WebClient webClient;
    private final OperatingSystemMXBean osBean;
    private final ConnectionProvider provider;

    public PerformanceMonitorFilter() {
        java.lang.management.OperatingSystemMXBean bean = ManagementFactory.getOperatingSystemMXBean();
        this.osBean = (bean instanceof OperatingSystemMXBean) ? (OperatingSystemMXBean) bean : null;

        // Configura um pool de conexões robusto para alta concorrência
        this.provider = ConnectionProvider.builder("metrics-pool")
                .maxConnections(1000)               // Permite mais conexões simultâneas
                .pendingAcquireMaxCount(200000)     // Aumenta drasticamente a fila de espera (buffer)
                .pendingAcquireTimeout(Duration.ofSeconds(180)) // Aumenta o tempo de espera para 3 minutos
                .build();

        this.webClient = WebClient.builder()
                .baseUrl("http://localhost:8002/sql")
                .clientConnector(new ReactorClientHttpConnector(HttpClient.create(provider)))
                .build();
    }

    @Override
    public void destroy() {
        // Garante o encerramento gracioso do pool de conexões ao desligar a aplicação
        this.provider.disposeLater().subscribe();
    }

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, WebFilterChain chain) {
        // --- ANTES DA REQUISIÇÃO ---
        long startNano = System.nanoTime();
        long startCpuTime = (osBean != null) ? osBean.getProcessCpuTime() : 0;
        long[] memInfoBefore = getSystemMemory();
        long memBefore = memInfoBefore[0];

        return chain.filter(exchange)
                .doFinally(signal -> recordMetrics(exchange, startNano, startCpuTime, memBefore).subscribe());
    }

    private Mono<Void> recordMetrics(ServerWebExchange exchange, long startNano, long startCpuTime, long memBefore) {
        return Mono.fromCallable(() -> {
            // --- DEPOIS DA REQUISIÇÃO ---
            long endNano = System.nanoTime();
            long endCpuTime = (osBean != null) ? osBean.getProcessCpuTime() : 0;
            long[] memInfoAfter = getSystemMemory();
            long memAfter = memInfoAfter[0];
            long memTotal = memInfoAfter[1];

            // CÁLCULO DOS DELTAS (DIFERENÇAS)
            long durationMs = (endNano - startNano) / 1_000_000;

            long durationNano = endNano - startNano;
            double cpuUsage = 0.0;
            if (durationNano > 0) {
                long cpuTimeUsed = endCpuTime - startCpuTime;
                cpuUsage = (double) cpuTimeUsed / durationNano * 100.0 / Runtime.getRuntime().availableProcessors();
            }

            long deltaMem = memAfter - memBefore; // Em Bytes

            double processCpuLoad = (osBean != null) ? osBean.getProcessCpuLoad() : 0.0;
            if (processCpuLoad < 0) processCpuLoad = 0.0;

            double cpuTemp = getCpuTemperature();

            return new Dados(
                String.valueOf(exchange.getRequest().getURI()),
                durationMs + " ms",
                String.format(Locale.US, "%.2f", processCpuLoad * 100),
                String.format(Locale.US, "%.2f", cpuUsage),  /// CPU
                String.format("%.1f°C", cpuTemp),
                (memAfter / (1024 * 1024)) + "MB / " + (memTotal / (1024 * 1024)) + "MB",
                deltaMem + " B",
                LocalDateTime.now().toString()
            );
        })
        .subscribeOn(Schedulers.boundedElastic())
        .flatMap(dados -> webClient
            .post()
            .bodyValue(dados)
            .retrieve()
            .bodyToMono(Void.class)
            .doOnError(e -> logger.warn("Falha ao enviar métrica para {}: {}", dados.url(), e.getMessage()))
            .onErrorResume(e -> Mono.empty())
        );
    }

    private double getCpuTemperature() {
        try {
            String path = "/sys/class/thermal/thermal_zone0/temp";
            if (Files.exists(Paths.get(path))) {
                String content = Files.readString(Paths.get(path)).trim();
                long tempMilli = Long.parseLong(content);
                return tempMilli / 1000.0;
            }
        } catch (Exception e) {
            // Ignora erros se não conseguir ler a temperatura
        }
        return 0.0;
    }

    private long[] getSystemMemory() {
        if (osBean != null) {
            long total = osBean.getTotalPhysicalMemorySize();
            long free = osBean.getFreePhysicalMemorySize();
            return new long[]{total - free, total};
        }
        return new long[]{Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory(), Runtime.getRuntime().maxMemory()};
    }
}