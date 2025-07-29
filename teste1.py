def projetar_dados_teste(
    df_ligacoes_filtered,
    df_rmarcadas_filtrado,
    df_rrealizadas_filtrado,
    df_cassinados_filtrado,
    df_metas_individuais,
    df_captação_mes,
    df_linhas_validas,
    valores,
    metas_acumuladas,
    multiplicador_mes,
    n_consultores,
    dias_selecionados,
    data_inicio,
    data_fim
):
    """
    Dashboard de Projeção de Dados com Design Profissional Dark Mode
    
    Mantém toda funcionalidade original com visual moderno e elegante
    Inclui correções para compatibilidade PyArrow e Plotly
    """
    
    import streamlit as st
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import re
    from datetime import datetime, timedelta

    # Função para limpar dados e evitar erros de serialização
    def clean_dataframe_for_display(df):
        """
        Limpa o DataFrame para evitar erros de serialização PyArrow
        Converte tipos problemáticos para string
        """
        df_clean = df.copy()
        
        # Identificar colunas problemáticas (object com tipos mistos)
        for col in df_clean.columns:
            if df_clean[col].dtype == 'object':
                # Converter para string para evitar problemas de serialização
                df_clean[col] = df_clean[col].astype(str)
                
        return df_clean

    # CSS personalizado para tema dark consistente
    st.markdown("""
    <style>
        /* Importar fonte moderna */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Headers de seção elegantes */
        .section-header-proj {
            font-size: 1.6rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 1.2rem;
            padding-bottom: 0.6rem;
            border-bottom: 2px solid #6366f1;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            font-family: 'Inter', sans-serif;
        }
        
        /* Cards de métricas aprimorados para projeção */
        .metric-card-proj {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            padding: 1.5rem;
            margin: 0.8rem 0;
            box-shadow: 0 8px 25px rgba(0,0,0,0.4);
            transition: all 0.3s ease;
            backdrop-filter: blur(10px);
        }
        
        .metric-card-proj:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 35px rgba(99, 102, 241, 0.2);
            border-color: rgba(99, 102, 241, 0.5);
        }
        
        /* Containers com bordas elegantes */
        .stContainer {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            border: 1px solid rgba(99, 102, 241, 0.2);
            border-radius: 16px;
            backdrop-filter: blur(10px);
        }
        
        /* Gráficos com tema escuro */
        .plotly-graph-div {
            border-radius: 16px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            background: rgba(31, 41, 55, 0.8);
            backdrop-filter: blur(10px);
        }
        
        /* Divisores elegantes */
        .section-divider-proj {
            height: 2px;
            background: linear-gradient(90deg, transparent, #6366f1, #8b5cf6, transparent);
            margin: 2rem 0;
            border: none;
            border-radius: 2px;
        }
        
        /* Radio buttons dark mode */
        .stRadio > div {
            background: rgba(31, 41, 55, 0.6);
            border-radius: 8px;
            padding: 0.5rem;
        }
        
        /* DataFrames estilizados */
        .stDataFrame {
            background: rgba(31, 41, 55, 0.8);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
        }
    </style>
    """, unsafe_allow_html=True)

    # Header da seção
    st.markdown('<div class="section-header-proj">📊 Dashboard de Projeção e Performance</div>', unsafe_allow_html=True)

    # Layout reorganizado com duas colunas principais
    col_1, col_2, col_funil, col_leg = st.columns([1, 1, 3, 3])

    # ================================
    # COLUNA 1: LIGAÇÕES + REUNIÕES REALIZADAS
    # ================================
    with col_1:
        st.markdown("**🔊 Ligações & Realizações**")
        
        for nome, valor, meta in [
            ("Ligações", df_ligacoes_filtered.shape[0], dias_selecionados * n_consultores * 60),
            ("Reuniões Realizadas", valores["Reuniões Realizadas"], metas_acumuladas["Reuniões Realizadas"])
        ]:
            # Calcular percentual para cores dinâmicas
            percentual = (valor / meta * 100) if meta > 0 else 0
            
            # Cores baseadas na performance
            if percentual >= 80:
                cor_principal = "#10b981"  # Verde
                cor_steps = ["#ef4444", "#f59e0b", "#10b981"]
            elif percentual >= 50:
                cor_principal = "#f59e0b"  # Amarelo
                cor_steps = ["#ef4444", "#f59e0b", "#10b981"]
            else:
                cor_principal = "#ef4444"  # Vermelho
                cor_steps = ["#ef4444", "#f59e0b", "#10b981"]

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=valor,
                number={
                    'valueformat': ',.0f',
                    'font': {'size': 24, 'color': '#f8fafc'}
                },
                title={
                    'text': f"<b>{nome}</b>", 
                    'font': {'size': 16, 'color': '#f8fafc', 'family': 'Inter'}
                },
                delta={
                    'reference': meta,
                    'valueformat': ',.0f',
                    'font': {'color': cor_principal}
                },
                gauge={
                    'axis': {
                        'range': [0, meta * 1.2], 
                        'tickwidth': 2, 
                        'tickcolor': "#94a3b8",
                        'tickfont': {'color': '#94a3b8', 'size': 10}
                    },
                    'bar': {'color': cor_principal, 'thickness': 0.3},
                    'bgcolor': "#1f2937",
                    'borderwidth': 2,
                    'bordercolor': "#374151",
                    'steps': [
                        {'range': [0, 0.5 * meta], 'color': "rgba(239, 68, 68, 0.3)"},
                        {'range': [0.5 * meta, 0.8 * meta], 'color': "rgba(245, 158, 11, 0.3)"},
                        {'range': [0.8 * meta, meta], 'color': "rgba(16, 185, 129, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "#f8fafc", 'width': 4},
                        'thickness': 0.8,
                        'value': meta
                    }
                }
            ))

            fig.update_layout(
                margin=dict(t=40, b=20, l=20, r=20),
                height=200,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#f8fafc')
            )

            st.plotly_chart(fig, use_container_width=True)

    # ================================
    # COLUNA 2: REUNIÕES MARCADAS + CONTRATOS ASSINADOS
    # ================================
    with col_2:
        st.markdown("**📅 Marcações & Contratos**")
        
        for nome in ["Reuniões Marcadas", "Contratos Assinados"]:
            valor = valores[nome]
            meta = metas_acumuladas[nome]
            
            # Calcular percentual para cores dinâmicas
            percentual = (valor / meta * 100) if meta > 0 else 0
            
            if percentual >= 80:
                cor_principal = "#10b981"
            elif percentual >= 50:
                cor_principal = "#f59e0b"
            else:
                cor_principal = "#ef4444"

            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=valor,
                number={
                    'valueformat': ',.0f',
                    'font': {'size': 24, 'color': '#f8fafc'}
                },
                title={
                    'text': f"<b>{nome}</b>", 
                    'font': {'size': 16, 'color': '#f8fafc', 'family': 'Inter'}
                },
                delta={
                    'reference': meta,
                    'valueformat': ',.0f',
                    'font': {'color': cor_principal}
                },
                gauge={
                    'axis': {
                        'range': [0, meta * 1.2], 
                        'tickwidth': 2, 
                        'tickcolor': "#94a3b8",
                        'tickfont': {'color': '#94a3b8', 'size': 10}
                    },
                    'bar': {'color': cor_principal, 'thickness': 0.3},
                    'bgcolor': "#1f2937",
                    'borderwidth': 2,
                    'bordercolor': "#374151",
                    'steps': [
                        {'range': [0, 0.5 * meta], 'color': "rgba(239, 68, 68, 0.3)"},
                        {'range': [0.5 * meta, 0.8 * meta], 'color': "rgba(245, 158, 11, 0.3)"},
                        {'range': [0.8 * meta, meta], 'color': "rgba(16, 185, 129, 0.3)"}
                    ],
                    'threshold': {
                        'line': {'color': "#f8fafc", 'width': 4},
                        'thickness': 0.8,
                        'value': meta
                    }
                }
            ))
            
            fig.update_layout(
                margin=dict(t=40, b=20, l=20, r=20),
                height=200,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Inter', color='#f8fafc')
            )
            
            st.plotly_chart(fig, use_container_width=True)

    # ================================
    # COLUNA 3: FUNIL DE CONVERSÃO APRIMORADO
    # ================================
    with col_funil:
        st.markdown("**🎯 Funil de Conversão**")
        
        etapas = list(valores.keys())
        quantidades = list(valores.values())

        # Taxas de conversão entre etapas
        taxas = []
        for i in range(len(quantidades) - 1):
            de = quantidades[i]
            para = quantidades[i + 1]
            taxa = (para / de) * 100 if de > 0 else 0
            taxas.append(f"{taxa:.1f}%")

        # Posições ajustadas para melhor visualização
        posicoes_y_etapas = [0.92, 0.55, 0.19]
        posicoes_y_taxas = [0.305, 0.687]

        # Criação do DataFrame base
        df_funnel = pd.DataFrame({
            "Etapa": etapas,
            "Quantidade": quantidades
        })

        # Gráfico base com cores do tema
        fig = px.funnel(
            df_funnel,
            y="Etapa",
            x="Quantidade",
            color_discrete_sequence=["#6366f1"]  # Cor do tema
        )

        for trace in fig.data:
            trace.text = None
            trace.texttemplate = ""
            trace.textinfo = "none"

        # Remove texto automático
        fig.update_traces(text=None, texttemplate="")

        # Anotações: Etapas com valores
        for i, (etapa, y) in enumerate(zip(etapas, posicoes_y_etapas)):
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=y,
                text=f"<b>{etapa}</b><br><span style='font-size:14px'>{quantidades[i]:,}</span>",
                showarrow=False,
                font=dict(size=16, color="#f8fafc", family="Inter")
            )

        # Anotações: Taxas de conversão
        for i, y in enumerate(posicoes_y_taxas):
            cor_taxa = "#10b981" if float(taxas[i].replace('%', '')) > 15 else "#f59e0b" if float(taxas[i].replace('%', '')) > 8 else "#ef4444"
            fig.add_annotation(
                xref="paper", yref="paper",
                x=0.5, y=y,
                text=f"⬇️ <span style='color:{cor_taxa}'><b>{taxas[i]}</b></span>",
                showarrow=False,
                font=dict(size=14, color="#f8fafc", family="Inter")
            )

        # Layout final
        fig.update_layout(
            title=dict(
                text="<b>Funil de Conversão</b>",
                font=dict(size=18, color="#f8fafc", family="Inter"),
                x=0.5
            ),
            margin=dict(t=60, b=20, l=20, r=20),
            height=420,
            showlegend=False,
            yaxis=dict(showticklabels=False, title=None),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        
        st.plotly_chart(fig, use_container_width=True)

        # Conversão total com destaque
        conv_final = round((quantidades[-1]/quantidades[0])*100, 1) if quantidades[0] != 0 else 0
        cor_conv_final = "#10b981" if conv_final > 3 else "#f59e0b" if conv_final > 1.5 else "#ef4444"
        
        st.markdown(
            f"""
            <div style='
                text-align: center; 
                font-size: 18px; 
                font-weight: bold;
                background: linear-gradient(135deg, {cor_conv_final}20, {cor_conv_final}10);
                border: 1px solid {cor_conv_final}40;
                border-radius: 12px;
                padding: 1rem;
                margin-top: 1rem;
                color: {cor_conv_final};
            '>
                🎯 Conversão Total: {conv_final:.2f}%
            </div>
            """,
            unsafe_allow_html=True
        )

    # ================================
    # COLUNA 4: GRÁFICOS TEMPORAIS
    # ================================
    with col_leg:
        st.markdown("**📈 Performance Temporal**")
        
        # GRÁFICO 1: Reuniões marcadas por dia
        dias = pd.date_range(start=data_inicio, end=data_fim, freq='B')
        meta_individual = 2
        meta_diaria_ajustada = meta_individual * n_consultores

        df_dia = (
            df_rmarcadas_filtrado.groupby("DATA")["CONSULTOR"]
            .count()
            .reindex(dias.date, fill_value=0)
            .reset_index()
            .rename(columns={"index": "DATA", "CONSULTOR": "REALIZADO"})
        )

        df_dia["LABEL"] = df_dia["DATA"].apply(lambda d: d.strftime("%d/%m"))

        fig = go.Figure()

        # Barras com gradiente
        fig.add_trace(go.Bar(
            x=df_dia["LABEL"],
            y=df_dia["REALIZADO"],
            name="Reuniões Marcadas",
            marker=dict(
                color=df_dia["REALIZADO"],
                colorscale=[[0, '#374151'], [0.5, '#6366f1'], [1, '#8b5cf6']],
                showscale=False,
                line=dict(color='#1f2937', width=1)
            ),
            text=df_dia["REALIZADO"],
            textposition="outside",
            textfont=dict(color='#f8fafc'),
            hovertemplate="<b>%{x}</b><br>Reuniões: %{y}<extra></extra>"
        ))

        # Linha da meta
        fig.add_trace(go.Scatter(
            x=df_dia["LABEL"],
            y=[meta_diaria_ajustada] * len(df_dia),
            mode="lines",
            name="Meta Diária",
            line=dict(color="#10b981", dash="dash", width=3),
            hovertemplate=f"<b>Meta: {meta_diaria_ajustada}</b><extra></extra>"
        ))

        fig.update_layout(
            title=dict(
                text="<b>Reuniões Marcadas por Dia vs Meta</b>",
                font=dict(size=16, color="#f8fafc", family="Inter"),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="Data (dias úteis)", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8')
            ),
            yaxis=dict(
                title=dict(text="Reuniões marcadas", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8'),
                range=[0, max(df_dia["REALIZADO"].max(), meta_diaria_ajustada) * 1.15]
            ),
            barmode='group',
            hovermode="x unified",
            showlegend=False,
            margin=dict(t=50, b=20, l=20, r=20),
            height=240,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )

        # Anotação da meta elegante
        fig.add_annotation(
            xref="paper", yref="y",
            x=0.99, y=meta_diaria_ajustada,
            text=f"Meta: {meta_diaria_ajustada}",
            showarrow=False,
            font=dict(size=12, color="#10b981", family="Inter"),
            bgcolor="rgba(16, 185, 129, 0.1)",
            bordercolor="#10b981",
            borderwidth=1,
            borderpad=5
        )

        st.plotly_chart(fig, use_container_width=True)

        # GRÁFICO 2: Performance acumulada
        dias_uteis = pd.bdate_range(start=data_inicio, end=data_fim)

        dados_real = {
            "Reuniões Marcadas": df_rmarcadas_filtrado,
            "Reuniões Realizadas": df_rrealizadas_filtrado,
            "Contratos Assinados": df_cassinados_filtrado
        }

        fig = go.Figure()

        cores_metricas = {
            "Reuniões Marcadas": "#6366f1",
            "Reuniões Realizadas": "#10b981", 
            "Contratos Assinados": "#f59e0b"
        }

        # Função para converter hex para rgba
        def hex_to_rgba(hex_color, alpha=0.1):
            """Converte cor hexadecimal para rgba"""
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"


        for i, (nome_metrica, df) in enumerate(dados_real.items()):
            # Conta diários (apenas dias úteis)
            df_dia = (
                df.groupby("DATA")["CONSULTOR"]
                .count()
                .reindex(dias_uteis.date, fill_value=0)
                .rename("REALIZADO")
                .reset_index()
                .rename(columns={"index": "DATA"})
            )

            cor_metrica = cores_metricas[nome_metrica]

            # Linha Realizado
            fig.add_trace(go.Scatter(
                x=df_dia["DATA"],
                y=df_dia["REALIZADO"].cumsum(),
                mode="lines+markers",
                name=f"{nome_metrica}",
                line=dict(color=cor_metrica, width=3),
                marker=dict(color=cor_metrica, size=6),
                fill="tozeroy",
                fillcolor=hex_to_rgba(cor_metrica, 0.1),
                visible=(i == 0),
                hovertemplate=f"<b>{nome_metrica}</b><br>Data: %{{x}}<br>Acumulado: %{{y}}<extra></extra>"
            ))

            # Linha de Meta Acumulada
            meta_diaria = {
                "Reuniões Marcadas" : 2 * n_consultores,
                "Reuniões Realizadas" : 1.4 * n_consultores,
                "Contratos Assinados" : 0.7 * n_consultores
            }
            meta_diaria = meta_diaria[nome_metrica]
            df_dia["META"] = [meta_diaria * (j + 1) for j in range(len(df_dia))]

            fig.add_trace(go.Scatter(
                x=df_dia["DATA"],
                y=df_dia["META"],
                mode="lines+markers",
                name=f"{nome_metrica} - Meta",
                line=dict(color=cor_metrica, dash="dot", width=2),
                marker=dict(color=cor_metrica, size=4, symbol="diamond"),
                visible=(i == 0),
                hovertemplate=f"<b>Meta {nome_metrica}</b><br>Data: %{{x}}<br>Meta: %{{y:.0f}}<extra></extra>"
            ))

        # Botões interativos estilizados
        buttons = []
        for i, nome_metrica in enumerate(dados_real.keys()):
            vis = [False] * (len(dados_real) * 2)
            vis[i*2] = True       # Realizado
            vis[i*2 + 1] = True   # Meta
            buttons.append(dict(
                label=nome_metrica,
                method="update",
                args=[{"visible": vis},
                    {"title": f"<b>{nome_metrica} - Performance Acumulada</b>"}]
            ))

        fig.update_layout(
            title=dict(
                text="<b>Reuniões Marcadas - Performance Acumulada</b>",
                font=dict(size=16, color="#f8fafc", family="Inter"),
                x=0.5
            ),
            xaxis=dict(
                title=dict(text="Data", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8'),
                range=[dias_uteis[0], dias_uteis[-1]]
            ),
            yaxis=dict(
                title=dict(text="Quantidade acumulada", font=dict(color='#f8fafc')),
                tickfont=dict(color='#94a3b8')
            ),
            height=280,
            hovermode="x unified",
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            updatemenus=[
                dict(
                    type="buttons",
                    direction="right",
                    x=0.5,
                    y=-0.15,
                    xanchor="center",
                    showactive=True,
                    bgcolor="rgba(31, 41, 55, 0.8)",
                    bordercolor="#6366f1",
                    borderwidth=1,
                    font=dict(
                        color="#6366f1",
                        size=10,
                        family="Inter"
                    ),
                    buttons=buttons
                )
            ],
            margin=dict(t=50, b=60, l=20, r=20)
        )

        st.plotly_chart(fig, use_container_width=True)


    # Divisor elegante
    st.markdown('<hr class="section-divider-proj">', unsafe_allow_html=True)

    # ================================
    # SEÇÃO DE RANKINGS
    # ================================
    st.markdown('<div class="section-header-proj">🏆 Rankings de Performance</div>', unsafe_allow_html=True)

    cols_rankings = st.columns(3)

    # RANKING 1: Ligações por consultor
    with cols_rankings[0]:
        st.markdown("**📞 Ligações por Consultor**")
        
        try:
            mapa_linha_consultor = df_linhas_validas.set_index("LINHA")["CONSULTOR"].to_dict()
            df_ligacoes_work = df_ligacoes_filtered.copy()
            df_ligacoes_work["Linha"] = df_ligacoes_work["Usuário"].str.extract(r"\((\d{10,})\s*-")
            df_ligacoes_work["Consultor"] = df_ligacoes_work["Linha"].map(mapa_linha_consultor)

            # Remover consultores NaN
            df_ligacoes_work = df_ligacoes_work[df_ligacoes_work["Consultor"].notna()]

            if not df_ligacoes_work.empty:
                df_agrupado = df_ligacoes_work["Consultor"].value_counts().reset_index()
                df_agrupado.columns = ["Consultor", "Número de Ligações"]
                df_agrupado = df_agrupado.sort_values(by="Número de Ligações", ascending=True)

                fig = go.Figure(go.Bar(
                    x=df_agrupado["Número de Ligações"],
                    y=df_agrupado["Consultor"],
                    orientation='h',
                    text=df_agrupado["Número de Ligações"],
                    textposition="outside",
                    textfont=dict(color='#f8fafc'),
                    marker=dict(
                        color=df_agrupado["Número de Ligações"],
                        colorscale=[[0, '#374151'], [0.5, '#6366f1'], [1, '#8b5cf6']],
                        showscale=False,
                        line=dict(color='#1f2937', width=1)
                    ),
                    hovertemplate="<b>%{y}</b><br>Ligações: %{x}<extra></extra>"
                ))

                fig.update_layout(
                    title=dict(
                        text="<b>Número de ligações por consultor</b>",
                        font=dict(size=14, color="#f8fafc", family="Inter"),
                        x=0.5
                    ),
                    xaxis=dict(
                        title=dict(text="Número de Ligações", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8')
                    ),
                    yaxis=dict(
                        title=dict(text="Consultor", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        automargin=True
                    ),
                    margin=dict(t=50, b=20, l=20, r=20),
                    height=350,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 Nenhum dado de ligação por consultor disponível")
                
        except Exception as e:
            st.error(f"⚠️ Erro ao processar dados de ligações: {str(e)}")
            st.info("📊 Dados de ligação podem estar em formato incompatível")

    # RANKINGS 2 e 3: Reuniões e Contratos
    rankings = [
        ("Reuniões Marcadas", df_rmarcadas_filtrado),
        ("Contratos Assinados", df_cassinados_filtrado)
    ]
    
    cores_rankings = ["#10b981", "#f59e0b"]
    
    for idx, (titulo, df) in enumerate(rankings):
        try:
            if not df.empty and "CONSULTOR" in df.columns:
                df_ranking = (
                    df["CONSULTOR"]
                    .value_counts()
                    .rename_axis("Consultor")
                    .reset_index(name="Quantidade")
                    .sort_values(by="Quantidade", ascending=True)
                )

                if not df_ranking.empty:
                    fig = go.Figure(go.Bar(
                        x=df_ranking["Quantidade"],
                        y=df_ranking["Consultor"],
                        orientation="h",
                        text=df_ranking["Quantidade"],
                        textposition="outside",
                        textfont=dict(color='#f8fafc'),
                        marker=dict(
                            color=cores_rankings[idx],
                            line=dict(color='#1f2937', width=1)
                        ),
                        hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<extra></extra>"
                    ))

                    fig.update_layout(
                        title=dict(
                            text=f"<b>{titulo}</b>",
                            font=dict(size=14, color="#f8fafc", family="Inter"),
                            x=0.5
                        ),
                        xaxis=dict(
                            title=dict(text="Quantidade", font=dict(color='#f8fafc')),
                            tickfont=dict(color='#94a3b8')
                        ),
                        yaxis=dict(
                            title=dict(text="Consultor", font=dict(color='#f8fafc')),
                            tickfont=dict(color='#94a3b8'),
                            automargin=True
                        ),
                        margin=dict(t=50, b=20, l=20, r=20),
                        height=350,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )

                    with cols_rankings[idx + 1]:
                        st.markdown(f"**{titulo}**")
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    with cols_rankings[idx + 1]:
                        st.markdown(f"**{titulo}**")
                        st.info("📊 Nenhum dado disponível")
            else:
                with cols_rankings[idx + 1]:
                    st.markdown(f"**{titulo}**")
                    st.info("📊 Dados não disponíveis")
        except Exception as e:
            with cols_rankings[idx + 1]:
                st.markdown(f"**{titulo}**")
                st.error(f"⚠️ Erro ao processar: {str(e)}")

    # Divisor elegante
    st.markdown('<hr class="section-divider-proj">', unsafe_allow_html=True)

    # ================================
    # RANKING DE CAPTAÇÃO
    # ================================
    st.markdown('<div class="section-header-proj">💰 Ranking de Captação</div>', unsafe_allow_html=True)

    try:
        df_cap = df_captação_mes.copy()
        df_metas = df_metas_individuais.copy()

        # Verificar se os DataFrames não estão vazios
        if df_cap.empty or df_metas.empty:
            st.warning("⚠️ Dados de captação ou metas não disponíveis")
        else:
            # Processamento dos dados (mantido original com tratamento de erro)
            df_cap["NOME"] = (
                df_cap["NOME"]
                .astype(str)
                .apply(lambda x: re.sub(r'\d+', '', x))
                .str.replace("#", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.upper()
            )

            df_metas["CONSULTOR"] = (
                df_metas["CONSULTOR"]
                .astype(str)
                .str.replace(" ", "", regex=False)
                .str.upper()
            )

            # Processamento seguro de valores monetários
            def safe_monetary_conversion(value):
                """Converte valores monetários de forma segura"""
                try:
                    if pd.isna(value) or value == '':
                        return 0.0
                    value_str = str(value)
                    # Remove formatação monetária
                    clean_value = (value_str
                                   .replace("R$", "")
                                   .replace(".", "")
                                   .replace(",", ".")
                                   .replace("- ", "-")
                                   .strip())
                    if clean_value == "" or clean_value == "-":
                        return 0.0
                    return float(clean_value)
                except (ValueError, TypeError):
                    return 0.0

            df_cap["CAPTACAO"] = df_cap["CAPTACAO"].apply(safe_monetary_conversion)

            # Merge com metas
            df = pd.merge(df_cap, df_metas, left_on="NOME", right_on="CONSULTOR", how="left")
            
            # Processamento seguro das metas
            for col in ["BOM", "OTIMO", "EXCEPCIONAL"]:
                if col in df.columns:
                    df[col] = df[col].apply(safe_monetary_conversion)

            df = df.sort_values(by="CAPTACAO", ascending=True)

            # Verificar se há dados após o processamento
            if df.empty:
                st.info("📊 Nenhum dado de captação disponível após processamento")
            else:
                # Gráfico aprimorado
                fig = go.Figure()

                # Barras de captação com cores baseadas no valor
                cores_captacao = []
                for valor in df["CAPTACAO"]:
                    if valor >= 0:
                        cores_captacao.append("#10b981")  # Verde para positivo
                    else:
                        cores_captacao.append("#ef4444")  # Vermelho para negativo

                fig.add_trace(go.Bar(
                    x=df["CAPTACAO"],
                    y=df["NOME"],
                    orientation="h",
                    text=df["CAPTACAO"].apply(lambda x: f"R$ {x:,.0f}".replace(",", ".")),
                    textposition="outside",
                    textfont=dict(color='#f8fafc', size=10),
                    marker=dict(
                        color=cores_captacao,
                        line=dict(color='#1f2937', width=1)
                    ),
                    name="Captação",
                    hovertemplate="<b>%{y}</b><br>Captação: R$ %{x:,.0f}<extra></extra>"
                ))

                # Adiciona marcadores de metas (se disponíveis)
                cores_metas = {"BOM": "#ef4444", "OTIMO": "#10b981", "EXCEPCIONAL": "#6366f1"}
                
                for idx, row in df.iterrows():
                    y_pos = row["NOME"]
                    for tipo, cor in cores_metas.items():
                        if tipo in row and pd.notnull(row[tipo]) and row[tipo] > 0:
                            valor_meta = row[tipo]
                            fig.add_shape(
                                type="line",
                                x0=valor_meta,
                                x1=valor_meta,
                                y0=idx - 0.4,
                                y1=idx + 0.4,
                                line=dict(color=cor, width=3),
                                xref="x",
                                yref="y"
                            )

                # Layout melhorado
                captacao_max = df["CAPTACAO"].max() if not df["CAPTACAO"].empty else 100000
                captacao_min = df["CAPTACAO"].min() if not df["CAPTACAO"].empty else -10000
                
                limite_x = captacao_max * 1.2 if captacao_max > 0 else captacao_max * 0.8
                limite_min = captacao_min * 1.2 if captacao_min < 0 else 0

                fig.update_layout(
                    title=dict(
                        text="<b>Ranking de Captação por Consultor (com Metas)</b>",
                        font=dict(size=18, color="#f8fafc", family="Inter"),
                        x=0.5
                    ),
                    xaxis=dict(
                        title=dict(text="Valor Captado (R$)", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        range=[limite_min, limite_x]
                    ),
                    yaxis=dict(
                        title=dict(text="Consultor", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8')
                    ),
                    height=600,
                    margin=dict(t=60, b=40, l=20, r=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                # Legenda das metas
                st.markdown("""
                **Legenda das Metas:**
                - 🔴 **BOM** (Linha Vermelha)
                - 🟢 **ÓTIMO** (Linha Verde)  
                - 🔵 **EXCEPCIONAL** (Linha Azul)
                """)

                st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Erro ao processar dados de captação: {str(e)}")
        st.info("💡 Verifique se os dados estão no formato correto para análise de captação")

    # Divisor elegante
    st.markdown('<hr class="section-divider-proj">', unsafe_allow_html=True)

    # ================================
    # SEÇÃO DE ANÁLISES DETALHADAS
    # ================================
    st.markdown('<div class="section-header-proj">📋 Análises Detalhadas</div>', unsafe_allow_html=True)

    cols_tabelas = st.columns(2)
    
    # ANÁLISE DE ORIGEM DOS LEADS
    with cols_tabelas[0]:
        with st.container(border=True):
            st.markdown("**🎯 Origem dos Leads**")
            cols_1 = st.columns([1, 2])

            with cols_1[0]:
                metrica_origem = st.radio(
                    "Selecione a etapa do funil:", 
                    [
                        "Reuniões Marcadas",
                        "Reuniões Realizadas", 
                        "Contratos Assinados"
                    ],
                    help="Escolha qual etapa analisar"
                )

                df_map = {
                    "Reuniões Marcadas": df_rmarcadas_filtrado,
                    "Reuniões Realizadas": df_rrealizadas_filtrado,
                    "Contratos Assinados": df_cassinados_filtrado
                }

                df_origem = df_map[metrica_origem]

                # Verificar se o DataFrame não está vazio
                if not df_origem.empty:
                    tabela_origens = (
                        df_origem["ORIGEM"]
                        .value_counts()
                        .rename_axis("Origem")
                        .to_frame(name="Quantidade")
                    )

                    if metrica_origem != "Contratos Assinados":
                        assinados_por_origem = (
                            df_cassinados_filtrado["ORIGEM"]
                            .value_counts()
                            .rename_axis("Origem")
                            .to_frame(name="Assinados")
                        )

                        tabela_origens = tabela_origens.join(assinados_por_origem, how="left")
                        tabela_origens["Assinados"] = tabela_origens["Assinados"].fillna(0)
                        tabela_origens["Conversão"] = (
                            tabela_origens["Assinados"] / tabela_origens["Quantidade"]
                        ).apply(lambda x: f"{x:.1%}" if x > 0 else "0%")

                        tabela_origens = tabela_origens.drop(columns=["Assinados"])
                else:
                    # DataFrame vazio - criar tabela vazia
                    tabela_origens = pd.DataFrame(columns=["Quantidade"])

            with cols_1[1]:
                # Limpar dados antes de exibir para evitar erros PyArrow
                if not tabela_origens.empty:
                    tabela_limpa = clean_dataframe_for_display(tabela_origens)
                    st.dataframe(tabela_limpa, use_container_width=True)
                else:
                    st.info("📊 Nenhum dado disponível para o período selecionado")

    # HISTOGRAMA DE LIGAÇÕES
    with cols_tabelas[1]:
        st.markdown("**⏰ Distribuição de Ligações por Hora**")
        
        # Verificar se há dados de ligação válidos
        if not df_ligacoes_filtered.empty and "Início da ligação" in df_ligacoes_filtered.columns:
            df_ligacoes_hist = df_ligacoes_filtered.copy()
            df_ligacoes_hist = df_ligacoes_hist[df_ligacoes_hist["Início da ligação"].notna()]

            if not df_ligacoes_hist.empty:
                # Converter para horas decimais
                df_ligacoes_hist['HoraDecimal'] = (
                    df_ligacoes_hist['Início da ligação'].dt.hour +
                    df_ligacoes_hist['Início da ligação'].dt.minute / 60
                )

                # Histograma moderno
                hist_fig = px.histogram(
                    df_ligacoes_hist, 
                    x='HoraDecimal', 
                    nbins=14, 
                    title='<b>Distribuição de Ligações por Hora do Dia</b>',
                    labels={'HoraDecimal': 'Hora do Dia', 'count': 'Número de Ligações'}, 
                    range_x=[7, 25],
                    color_discrete_sequence=['#6366f1']
                )

                # Estética aprimorada
                hist_fig.update_traces(
                    marker_line_width=2, 
                    marker_line_color='#1f2937',
                    texttemplate='%{y}',
                    textposition='outside',
                    textfont=dict(color='#f8fafc')
                )
                
                hist_fig.update_layout(
                    title=dict(
                        font=dict(size=16, color="#f8fafc", family="Inter"),
                        x=0.5
                    ),
                    xaxis=dict(
                        title=dict(text="Hora do Dia", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8'),
                        tickmode='linear', 
                        dtick=1
                    ),
                    yaxis=dict(
                        title=dict(text="Número de Ligações", font=dict(color='#f8fafc')),
                        tickfont=dict(color='#94a3b8')
                    ),
                    bargap=0.1,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    margin=dict(t=50, b=20, l=20, r=20)
                )

                st.plotly_chart(hist_fig, use_container_width=True)
            else:
                st.info("📊 Nenhuma ligação com horário válido encontrada")
        else:
            st.info("📊 Dados de ligação não disponíveis")

    # Footer informativo
    st.markdown("---")
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-top: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.2);
    ">
        <div style="color: #f8fafc; font-size: 1rem; font-weight: 600; margin-bottom: 0.5rem;">
            📊 Dashboard de Projeção - Modo Noturno (Versão Corrigida)
        </div>
        <div style="color: #94a3b8; font-size: 0.8rem; margin-bottom: 0.5rem;">
            Análise completa de performance e projeções • Atualizado: {datetime.now().strftime("%d/%m/%Y %H:%M")}
        </div>
        <div style="color: #6366f1; font-size: 0.7rem; display: flex; justify-content: center; gap: 15px;">
            <span>✅ PyArrow: Compatível</span>
            <span>✅ Plotly: Corrigido</span>
            <span>✅ Tratamento: Robusto</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
