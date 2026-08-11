import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Dashboard Analisis Pola Kerja - PLN Unit Pelayanan Garut",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for enterprise look
st.markdown("""
    <style>
    .main-header {
        color: #003366;
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 0.2em;
    }
    .sub-header {
        color: #666666;
        font-size: 1.1em;
        margin-bottom: 1.5em;
        font-weight: 500;
    }
    .metric-box {
        background-color: #f8f9fa;
        padding: 1em;
        border-radius: 0.5em;
        border-left: 4px solid #003366;
    }
    .tab-header {
        color: #003366;
        font-size: 1.4em;
        font-weight: 600;
        margin-bottom: 1.5em;
        border-bottom: 2px solid #003366;
        padding-bottom: 0.5em;
    }
    .info-box {
        background-color: #e8f4f8;
        border: 1px solid #b3d9e8;
        padding: 1em;
        border-radius: 0.5em;
        color: #003366;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        padding: 1em;
        border-radius: 0.5em;
        color: #856404;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">DASHBOARD ANALISIS POLA KERJA PEMBACAAN METER</div>',
            unsafe_allow_html=True)
st.markdown('<div class="sub-header">PT PLN (Persero) - Unit Pelayanan Garut (UNITUP 53277)</div>',
            unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("---")
st.sidebar.header("DATA INPUT")
uploaded_file = st.sidebar.file_uploader("Unggah File Data (Format: .xlsx)", type="xlsx")
st.sidebar.markdown("---")

if uploaded_file is not None:
    # Read data
    df = pd.read_excel(uploaded_file)

    # Parse WAKTU column
    def parse_waktu(waktu_str):
        if pd.isna(waktu_str):
            return None
        try:
            parts = str(waktu_str).strip().split()
            if len(parts) == 2:
                days = int(parts[0])
                time_parts = parts[1].split(':')
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
                total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
                return total_seconds
        except:
            pass
        return None

    # Data processing
    df['WAKTU_SECONDS'] = df['WAKTU'].apply(parse_waktu)
    df['DURASI_MENIT'] = df['WAKTU_SECONDS'] / 60
    df['DURASI_KATEGORI'] = pd.cut(df['DURASI_MENIT'],
                                   bins=[0, 1, 5, 10, 30, 60, float('inf')],
                                   labels=['<1 min', '1-5 min', '5-10 min',
                                          '10-30 min', '30-60 min', '>60 min'])

    # Parse date & time
    df['DATETIME'] = pd.to_datetime(df['TGLBACA'], dayfirst=True)
    df['TANGGAL'] = df['DATETIME'].dt.date
    df['JAM'] = df['DATETIME'].dt.hour
    df['HARI'] = df['DATETIME'].dt.day_name()
    df['MENIT'] = df['DATETIME'].dt.minute

    # Ensure coordinate columns are numeric
    df['LATITUDE'] = pd.to_numeric(df['LATITUDE'], errors='coerce')
    df['LONGITUDE'] = pd.to_numeric(df['LONGITUDE'], errors='coerce')

    # Location validation (Garut area bounds)
    df['LOKASI_VALID'] = (
        df['LATITUDE'].between(-7.9, -7.3, inclusive='both') &
        df['LONGITUDE'].between(107.4, 108.0, inclusive='both')
    )

    # Shift classification
    def classify_shift(hour):
        if 6 <= hour < 12:
            return 'Pagi (06:00-12:00)'
        elif 12 <= hour < 17:
            return 'Siang (12:00-17:00)'
        else:
            return 'Sore/Malam (17:00+)'

    df['SHIFT'] = df['JAM'].apply(classify_shift)

    # Efficiency scoring
    def efficiency_score(durasi):
        if pd.isna(durasi):
            return None
        if durasi < 1:
            return 'Sangat Baik'
        elif durasi < 5:
            return 'Baik'
        elif durasi < 10:
            return 'Cukup'
        elif durasi < 30:
            return 'Lambat'
        else:
            return 'Sangat Lambat'

    df['EFFICIENCY'] = df['DURASI_MENIT'].apply(efficiency_score)

    # Color mapping for efficiency
    efficiency_colors = {
        'Sangat Baik': '#2ecc71',
        'Baik': '#3498db',
        'Cukup': '#f39c12',
        'Lambat': '#e74c3c',
        'Sangat Lambat': '#c0392b'
    }

    # === TAB STRUCTURE ===
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "RINGKASAN EKSEKUTIF",
        "DISTRIBUSI WAKTU KERJA",
        "ANALISIS POLA KERJA PEGAWAI",
        "EVALUASI EFISIENSI",
        "ANALISIS GEOGRAFIS",
        "DATA DETAIL"
    ])

    # === TAB 1: RINGKASAN ===
    with tab1:
        st.markdown('<div class="tab-header">RINGKASAN EKSEKUTIF</div>', unsafe_allow_html=True)

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                label="Total Aktivitas Pembacaan",
                value=f"{len(df):,}",
                delta=None
            )

        with col2:
            avg_duration = df['DURASI_MENIT'].mean()
            st.metric(
                label="Durasi Rata-rata",
                value=f"{avg_duration:.1f} menit"
            )

        with col3:
            median_duration = df['DURASI_MENIT'].median()
            st.metric(
                label="Durasi Median",
                value=f"{median_duration:.1f} menit"
            )

        with col4:
            min_max = f"{df['DURASI_MENIT'].min():.1f} - {df['DURASI_MENIT'].max():.1f} menit"
            st.metric(
                label="Rentang Durasi",
                value=min_max
            )

        with col5:
            valid_pct = (df['LOKASI_VALID'].sum() / len(df)) * 100 if len(df) else 0
            st.metric(
                label="Lokasi Valid",
                value=f"{valid_pct:.1f}%",
                delta=f"{df['LOKASI_VALID'].sum()} dari {len(df)}"
            )

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Distribusi Efisiensi Pegawai**")
            eff_dist = df['EFFICIENCY'].value_counts()
            eff_order = ['Sangat Baik', 'Baik', 'Cukup', 'Lambat', 'Sangat Lambat']
            eff_dist = eff_dist.reindex([x for x in eff_order if x in eff_dist.index])

            fig_eff = go.Figure(data=[
                go.Bar(
                    x=eff_dist.index,
                    y=eff_dist.values,
                    marker=dict(color=[efficiency_colors.get(cat, '#95a5a6') for cat in eff_dist.index])
                )
            ])
            fig_eff.update_layout(
                showlegend=False,
                hovermode='x unified',
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Kategori Efisiensi",
                yaxis_title="Jumlah Aktivitas",
                plot_bgcolor='rgba(240, 240, 240, 0.5)',
                xaxis_showgrid=False
            )
            st.plotly_chart(fig_eff, use_container_width=True)

        with col2:
            st.markdown("**Tren Aktivitas Per Hari**")
            daily_count = df.groupby('TANGGAL').size().reset_index(name='Jumlah')

            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=daily_count['TANGGAL'],
                y=daily_count['Jumlah'],
                mode='lines+markers',
                line=dict(color='#003366', width=2),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(0, 51, 102, 0.1)'
            ))
            fig_trend.update_layout(
                showlegend=False,
                hovermode='x unified',
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Tanggal",
                yaxis_title="Total Aktivitas",
                plot_bgcolor='rgba(240, 240, 240, 0.5)',
                xaxis_showgrid=False
            )
            st.plotly_chart(fig_trend, use_container_width=True)

    # === TAB 2: DISTRIBUSI WAKTU ===
    with tab2:
        st.markdown('<div class="tab-header">ANALISIS DISTRIBUSI WAKTU KERJA</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Rata-rata Durasi Berdasarkan Jam Operasional**")
            hourly_dur = df.groupby('JAM')['DURASI_MENIT'].mean().reset_index()

            fig_hourly = go.Figure()
            fig_hourly.add_trace(go.Bar(
                x=hourly_dur['JAM'],
                y=hourly_dur['DURASI_MENIT'],
                marker=dict(color='#003366'),
                hovertemplate='<b>Jam %{x}:00</b><br>Rata-rata: %{y:.2f} menit<extra></extra>'
            ))
            fig_hourly.update_layout(
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Jam Kerja",
                yaxis_title="Durasi (menit)",
                plot_bgcolor='rgba(240, 240, 240, 0.5)',
                xaxis=dict(dtick=1)
            )
            st.plotly_chart(fig_hourly, use_container_width=True)

        with col2:
            st.markdown("**Rata-rata Durasi Berdasarkan Shift**")
            shift_dur = df.groupby('SHIFT')['DURASI_MENIT'].mean().reset_index()
            shift_order = ['Pagi (06:00-12:00)', 'Siang (12:00-17:00)', 'Sore/Malam (17:00+)']
            shift_dur = shift_dur.set_index('SHIFT').reindex(shift_order).reset_index()

            fig_shift = go.Figure()
            fig_shift.add_trace(go.Bar(
                x=shift_dur['SHIFT'],
                y=shift_dur['DURASI_MENIT'],
                marker=dict(color=['#2ecc71', '#3498db', '#e67e22']),
                hovertemplate='<b>%{x}</b><br>Rata-rata: %{y:.2f} menit<extra></extra>'
            ))
            fig_shift.update_layout(
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Shift Kerja",
                yaxis_title="Durasi (menit)",
                plot_bgcolor='rgba(240, 240, 240, 0.5)'
            )
            st.plotly_chart(fig_shift, use_container_width=True)

        st.markdown("---")

        st.markdown("**Pola Durasi: Jam x Tanggal (Heatmap)**")
        heatmap_data = df.pivot_table(values='DURASI_MENIT', index='JAM', columns='TANGGAL', aggfunc='mean')

        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='Blues',
            hovertemplate='Tanggal: %{x}<br>Jam: %{y}:00<br>Durasi: %{z:.1f} menit<extra></extra>'
        ))
        fig_heatmap.update_layout(
            height=400,
            margin=dict(l=60, r=40, t=40, b=80),
            xaxis_title="Tanggal",
            yaxis_title="Jam Kerja"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # === TAB 3: POLA KERJA PEGAWAI ===
    with tab3:
        st.markdown('<div class="tab-header">ANALISIS POLA KERJA PEGAWAI</div>', unsafe_allow_html=True)

        st.markdown("**Statistik Produktivitas Per Pegawai**")
        productivity = df.groupby('IDPEL').agg({
            'DURASI_MENIT': ['count', 'mean', 'std'],
            'LOKASI_VALID': 'sum'
        }).round(2)
        productivity.columns = ['Jumlah_Aktivitas', 'Rata_Rata_Durasi', 'Std_Dev', 'Lokasi_Valid']
        productivity = productivity.sort_values('Jumlah_Aktivitas', ascending=False)

        # Format display
        productivity_display = productivity.copy()
        productivity_display.columns = ['Jumlah Aktivitas', 'Rata-rata (menit)', 'Std Dev', 'Lokasi Valid']
        st.dataframe(productivity_display.head(15), use_container_width=True, height=400)

        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Distribusi Beban Kerja Per Hari**")
            daily_workload = df.groupby('TANGGAL').size().reset_index(name='Jumlah')

            fig_workload = go.Figure()
            fig_workload.add_trace(go.Box(
                y=df['DURASI_MENIT'],
                name='Durasi Aktivitas',
                marker=dict(color='#3498db')
            ))
            fig_workload.update_layout(
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40),
                yaxis_title="Durasi (menit)",
                plot_bgcolor='rgba(240, 240, 240, 0.5)'
            )
            st.plotly_chart(fig_workload, use_container_width=True)

        with col2:
            st.markdown("**Tren Durasi Rata-rata Per Hari**")
            daily_avg = df.groupby('TANGGAL')['DURASI_MENIT'].mean().reset_index()

            fig_prod_trend = go.Figure()
            fig_prod_trend.add_trace(go.Scatter(
                x=daily_avg['TANGGAL'],
                y=daily_avg['DURASI_MENIT'],
                mode='lines+markers',
                line=dict(color='#e74c3c', width=2),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.1)'
            ))
            fig_prod_trend.update_layout(
                showlegend=False,
                hovermode='x unified',
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Tanggal",
                yaxis_title="Durasi Rata-rata (menit)",
                plot_bgcolor='rgba(240, 240, 240, 0.5)'
            )
            st.plotly_chart(fig_prod_trend, use_container_width=True)

    # === TAB 4: ANALISIS EFISIENSI ===
    with tab4:
        st.markdown('<div class="tab-header">EVALUASI EFISIENSI & DETEKSI ANOMALI</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Kategori Efisiensi Aktivitas**")
            eff_cat = df['EFFICIENCY'].value_counts()
            eff_order = ['Sangat Baik', 'Baik', 'Cukup', 'Lambat', 'Sangat Lambat']
            eff_cat = eff_cat.reindex([x for x in eff_order if x in eff_cat.index])

            fig_eff_pie = go.Figure(data=[go.Pie(
                labels=eff_cat.index,
                values=eff_cat.values,
                marker=dict(colors=[efficiency_colors.get(cat, '#95a5a6') for cat in eff_cat.index]),
                hovertemplate='<b>%{label}</b><br>Jumlah: %{value}<br>Persentase: %{percent}<extra></extra>'
            )])
            fig_eff_pie.update_layout(
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig_eff_pie, use_container_width=True)

        with col2:
            st.markdown("**Distribusi Kategori Durasi**")
            dur_cat = df['DURASI_KATEGORI'].value_counts().sort_index().reset_index()
            dur_cat.columns = ['Kategori', 'Jumlah']

            fig_dur_cat = go.Figure()
            fig_dur_cat.add_trace(go.Bar(
                x=dur_cat['Kategori'],
                y=dur_cat['Jumlah'],
                marker=dict(color='#16a085'),
                hovertemplate='<b>%{x}</b><br>Jumlah: %{y}<extra></extra>'
            ))
            fig_dur_cat.update_layout(
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Rentang Durasi",
                yaxis_title="Jumlah Aktivitas",
                plot_bgcolor='rgba(240, 240, 240, 0.5)'
            )
            st.plotly_chart(fig_dur_cat, use_container_width=True)

        st.markdown("---")
        st.markdown("**Deteksi Aktivitas Anomali (Durasi Tidak Wajar)**")

        Q1 = df['DURASI_MENIT'].quantile(0.25)
        Q3 = df['DURASI_MENIT'].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = df[(df['DURASI_MENIT'] < lower_bound) | (df['DURASI_MENIT'] > upper_bound)]

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Aktivitas Anomali", len(outliers), f"{(len(outliers)/len(df)*100):.1f}% dari total")
        with col2:
            st.metric("Batas Normal", f"{lower_bound:.1f} - {upper_bound:.1f} menit")

        if len(outliers) > 0:
            st.markdown("**Detail Aktivitas Anomali (Maksimal 20 Data)**")
            display_outliers = outliers[['NOMOR', 'IDPEL', 'TGLBACA', 'DURASI_MENIT', 'EFFICIENCY', 'LOKASI_VALID']].head(20).copy()
            display_outliers.columns = ['Nomor', 'ID Pel', 'Tanggal Baca', 'Durasi (menit)', 'Efisiensi', 'Lokasi Valid']
            st.dataframe(display_outliers, use_container_width=True, height=400)
        else:
            st.info("Tidak ada aktivitas anomali terdeteksi dalam dataset.")

    # === TAB 5: ANALISIS GEOGRAFIS ===
    with tab5:
        st.markdown('<div class="tab-header">ANALISIS GEOGRAFIS POLA KERJA</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Peta Sebaran Aktivitas Pembacaan Meter**")
            lat_center = df['LATITUDE'].mean()
            lon_center = df['LONGITUDE'].mean()

            m = folium.Map(location=[lat_center, lon_center], zoom_start=13, tiles='OpenStreetMap')

            # Add boundary rectangle for Garut area
            folium.Rectangle(
                bounds=[[-7.9, 107.4], [-7.3, 108.0]],
                color='#003366',
                fill=True,
                fillColor='#003366',
                fillOpacity=0.1,
                weight=2,
                popup='Area Layanan Garut',
                dash_array='5, 5'
            ).add_to(m)

            for idx, row in df.iterrows():
                if row['LOKASI_VALID']:
                    color = '#2ecc71'
                    prefix = 'Valid'
                else:
                    color = '#e74c3c'
                    prefix = 'Invalid'

                folium.CircleMarker(
                    location=[row['LATITUDE'], row['LONGITUDE']],
                    radius=3,
                    popup=f"Durasi: {row['DURASI_MENIT']:.1f} min | Status: {prefix}",
                    tooltip=f"{row['DURASI_MENIT']:.1f} min",
                    color=color,
                    fill=True,
                    fillOpacity=0.7,
                    weight=1
                ).add_to(m)

            st_folium(m, width=700, height=500)

        with col2:
            st.markdown("**Validasi Lokasi Geografis**")

            valid_count = df['LOKASI_VALID'].sum()
            invalid_count = len(df) - valid_count
            valid_pct = (valid_count / len(df)) * 100 if len(df) else 0

            st.metric("Lokasi Valid (Garut)", f"{valid_pct:.1f}%", f"{valid_count} dari {len(df)} aktivitas")

            st.markdown("---")
            st.markdown("**Durasi Rata-rata Berdasarkan Validasi Lokasi**")

            loc_analysis = df.groupby('LOKASI_VALID')['DURASI_MENIT'].agg(['count', 'mean']).reset_index()
            loc_analysis['Status'] = loc_analysis['LOKASI_VALID'].map({True: 'Di Dalam Area', False: 'Di Luar Area'})

            fig_loc = go.Figure()
            fig_loc.add_trace(go.Bar(
                x=loc_analysis['Status'],
                y=loc_analysis['mean'],
                marker=dict(color=['#2ecc71', '#e74c3c']),
                text=loc_analysis['count'],
                texttemplate='n=%{text}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Rata-rata: %{y:.2f} menit<extra></extra>'
            ))
            fig_loc.update_layout(
                showlegend=False,
                margin=dict(l=40, r=40, t=40, b=40),
                xaxis_title="Status Lokasi",
                yaxis_title="Durasi Rata-rata (menit)",
                plot_bgcolor='rgba(240, 240, 240, 0.5)'
            )
            st.plotly_chart(fig_loc, use_container_width=True)

    # === TAB 6: DATA DETAIL ===
    with tab6:
        st.markdown('<div class="tab-header">DATA DETAIL AKTIVITAS PEMBACAAN</div>', unsafe_allow_html=True)

        st.markdown("**Filter Data**")
        col1, col2, col3 = st.columns(3)

        with col1:
            selected_date = st.multiselect("Tanggal", sorted(df['TANGGAL'].unique(), reverse=True))

        with col2:
            selected_shift = st.multiselect("Shift", ['Pagi (06:00-12:00)', 'Siang (12:00-17:00)', 'Sore/Malam (17:00+)'])

        with col3:
            selected_eff = st.multiselect("Efisiensi", ['Sangat Baik', 'Baik', 'Cukup', 'Lambat', 'Sangat Lambat'])

        # Filter data
        filtered_df = df.copy()
        if selected_date:
            filtered_df = filtered_df[filtered_df['TANGGAL'].isin(selected_date)]
        if selected_shift:
            filtered_df = filtered_df[filtered_df['SHIFT'].isin(selected_shift)]
        if selected_eff:
            filtered_df = filtered_df[filtered_df['EFFICIENCY'].isin(selected_eff)]

        # Display columns
        display_cols = ['NOMOR', 'IDPEL', 'TGLBACA', 'DURASI_MENIT',
                        'JAM', 'SHIFT', 'EFFICIENCY', 'LATITUDE', 'LONGITUDE', 'LOKASI_VALID']

        display_data = filtered_df[display_cols].copy()
        display_data.columns = ['Nomor', 'ID Pel', 'Tanggal Baca', 'Durasi (menit)',
                                'Jam', 'Shift', 'Efisiensi', 'Latitude', 'Longitude', 'Lokasi Valid']

        st.dataframe(display_data, use_container_width=True, height=600)

        st.markdown(f"**Total Record: {len(filtered_df)} dari {len(df)} data**")

else:
    st.markdown('<div class="info-box">Silakan unggah file data Excel pada sidebar untuk memulai analisis. File harus berisi kolom: WAKTU, LATITUDE, LONGITUDE, TGLBACA, IDPEL</div>',
                unsafe_allow_html=True)