package br.com.Busca.rebozitory;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.Scanner;

import br.com.Busca.processos.ProcessoMarca;

public class LerXml {

    public List<ProcessoMarca> lerMarcaXml(String nome){

        int n = 2879;
        List<ProcessoMarca> lista = new ArrayList<>();
        try{
        File arquivo = new File("arquivo/marca/RM"+n+".xml");
        Scanner sca = new Scanner(arquivo);

        ProcessoMarca m = null;

        // ler arquivo
        while(sca.hasNextLine()){
            String linha = sca.nextLine().trim();

            // nomero do processor
            if(linha.startsWith("<processo")){
                m = new ProcessoMarca();
                String numero = extrairAtributo(linha, "numero");
                if (numero != null) {
                    m.setNumnero(Integer.parseInt(numero));
                }
            }

            if (m != null) {
                if(linha.startsWith("<despacho")){
                    m.setCodigo(extrairAtributo(linha, "codigo"));
                    m.setNome(extrairAtributo(linha, "nome"));
                }
                
                if(linha.startsWith("<titular")){
                    m.setNomeRazaoSocial(extrairAtributo(linha, "nome-razao-social"));
                    m.setPais(extrairAtributo(linha, "pais"));
                    m.setUf(extrairAtributo(linha, "uf"));
                }

                if(linha.startsWith("<classe-nice")){
                    m.setClase(extrairAtributo(linha, "codigo"));
                }

                if(linha.startsWith("<especificacao>")){
                    m.setEspecificao(extrairValorTag(linha, "especificacao"));
                }

                if(linha.startsWith("<status>")){
                    m.setEstatos(extrairValorTag(linha, "status"));
                }

                if(linha.startsWith("<procurador>")){
                    m.setProcurado(extrairValorTag(linha, "procurador"));
                }

                if(linha.startsWith("</processo>")){
                    if (nome == null || nome.isEmpty() || (m.getNomeRazaoSocial() != null && m.getNomeRazaoSocial().toLowerCase().contains(nome.toLowerCase()))) {
                        lista.add(m);
                    }
                    m = null;
                }
            }
        }
        sca.close();
        }catch (Exception e){
            System.err.println(e);
            
        }
        return lista;
    }

    private String extrairAtributo(String linha, String atributo) {
        String chave = atributo + "=\"";
        int inicio = linha.indexOf(chave);
        if (inicio != -1) {
            inicio += chave.length();
            int fim = linha.indexOf("\"", inicio);
            if (fim != -1) {
                return linha.substring(inicio, fim);
            }
        }
        return null;
    }

    private String extrairValorTag(String linha, String tag) {
        String tagInicio = "<" + tag + ">";
        String tagFim = "</" + tag + ">";
        int inicio = linha.indexOf(tagInicio);
        if (inicio != -1) {
            inicio += tagInicio.length();
            int fim = linha.indexOf(tagFim, inicio);
            if (fim != -1) {
                return linha.substring(inicio, fim);
            }
        }
        return null;
    }
}
