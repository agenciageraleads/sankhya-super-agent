<%@ page language="java" contentType="text/html; charset=ISO-8859-1" pageEncoding="UTF-8" isELIgnored="false" %>
    <!DOCTYPE html>
    <%@ taglib uri="http://java.sun.com/jstl/core_rt" prefix="c" %>
        <%@ taglib prefix="snk" uri="/WEB-INF/tld/sankhyaUtil.tld" %>
            <html>

            <head>
                <title>Sankhya Super Agent (SSA)</title>
                <!-- Carrega bibliotecas nativas do Sankhya -->
                <snk:load />

                <style>
                    body,
                    html {
                        margin: 0;
                        padding: 0;
                        width: 100%;
                        height: 100%;
                        overflow: hidden;
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                        background-color: #f0f2f5;
                    }

                    #ssa-container {
                        display: flex;
                        flex-direction: column;
                        width: 100%;
                        height: 100%;
                    }

                    .header {
                        background-color: #fff;
                        padding: 10px 15px;
                        border-bottom: 1px solid #ddd;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                        height: 40px;
                    }

                    .header-title {
                        font-weight: bold;
                        color: #333;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }

                    #iframe-ssa {
                        flex-grow: 1;
                        border: none;
                        width: 100%;
                        height: calc(100% - 40px);
                    }

                    .status-badge {
                        background-color: #e0e0e0;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 11px;
                        color: #555;
                    }
                </style>

                <script>
                    // Função nativa do gadget para recarregar se necessário
                    function refreshSSA() {
                        var iframe = document.getElementById('iframe-ssa');
                        iframe.src = iframe.src;
                    }

                    // Listener para pegar contexto do Sankhya (se o usuário filtrar algo no Dashboard)
                    // Isso permite, no futuro, que o SSA saiba qual Empresa/Parceiro está selecionado

                    function queryParams() {
                        var params = [];

                        // Verifica filtros do Dashboard Sankhya e repassa ao SSA
                        if ("${CODEMP}" && "${CODEMP}".indexOf("$") === -1) {
                            params.push("codemp=${CODEMP}");
                        }
                        if ("${CODPARC}" && "${CODPARC}".indexOf("$") === -1) {
                            params.push("codparc=${CODPARC}");
                        }
                        if ("${DTNEG}" && "${DTNEG}".indexOf("$") === -1) {
                            params.push("data=${DTNEG}");
                        }

                        return params.length > 0 ? "&" + params.join("&") : "";
                    }

                    function init() {
                        // URL Base do Agente (Ajuste o IP conforme a rede)
                        var baseUrl = "http://192.168.100.111:8501/?embed=true";

                        // Adiciona contexto do Sankhya
                        var finalUrl = baseUrl + queryParams();

                        console.log("SSA Gadget Loaded: " + finalUrl);
                        document.getElementById('iframe-ssa').src = finalUrl;
                    }
                </script>
            </head>

            <body onload="init()">

                <div id="ssa-container">
                    <!-- O iframe carrega a aplicação Streamlit -->
                    <!-- Substitua o IP abaixo pelo IP do seu servidor onde o SSA roda -->
                    <iframe id="iframe-ssa" title="Sankhya Super Agent" src=""></iframe>
                </div>

            </body>

            </html>