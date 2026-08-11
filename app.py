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


def render_dashboard(df, tanggal_label):
    """Render the complete dashboard for one date."""
    st.markdown(
        f'<div class="sub-header">PT PLN (Persero) - Unit Pelayanan Garut '
        f'(UNITUP 53277) — {tanggal_label}</div>',
        unsafe_allow_html=True
    )

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


# Sidebar
st.sidebar.markdown("---")
st.sidebar.header("DATA INPUT")
uploaded_file = st.sidebar.file_uploader(
    "Unggah File Data (Format: .xlsx)",
    type=["xlsx"]
)
st.sidebar.markdown("---")

if uploaded_file is not None:
    try:
        # Read data
        df = pd.read_excel(uploaded_file)

        required_cols = ["NOMOR", "WAKTU", "LATITUDE", "LONGITUDE", "TGLBACA", "IDPEL"]
        missing_cols = [c for c in required_cols if c not in df.columns]

        if missing_cols:
            st.error("Kolom berikut tidak ditemukan: " + ", ".join(missing_cols))
            st.stop()

        # Parse WAKTU column
        def parse_waktu(waktu_str):
            if pd.isna(waktu_str):
                return None
            try:
                parts = str(waktu_str).strip().split()
                if len(parts) == 2:
                    days = int(parts[0])
                    time_parts = parts[1].split(":")
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2]) if len(time_parts) > 2 else 0
                    return days * 86400 + hours * 3600 + minutes * 60 + seconds
            except (ValueError, TypeError):
                return None
            return None

        df["WAKTU_SECONDS"] = df["WAKTU"].apply(parse_waktu)
        df["DURASI_MENIT"] = df["WAKTU_SECONDS"] / 60

        df["DURASI_KATEGORI"] = pd.cut(
            df["DURASI_MENIT"],
            bins=[0, 1, 5, 10, 30, 60, float("inf")],
            labels=["<1 min", "1-5 min", "5-10 min", "10-30 min", "30-60 min", ">60 min"]
        )

        # Parse date & time
        df["DATETIME"] = pd.to_datetime(df["TGLBACA"], dayfirst=True, errors="coerce")
        df["TANGGAL"] = df["DATETIME"].dt.date
        df["JAM"] = df["DATETIME"].dt.hour
        df["HARI"] = df["DATETIME"].dt.day_name()
        df["MENIT"] = df["DATETIME"].dt.minute

        # Coordinate validation
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        df["LOKASI_VALID"] = (
            df["LATITUDE"].between(-7.9, -7.3, inclusive="both")
            & df["LONGITUDE"].between(107.4, 108.0, inclusive="both")
        )

        # Shift classification
        def classify_shift(hour):
            if pd.isna(hour):
                return "Tidak diketahui"
            if 6 <= hour < 12:
                return "Pagi (06:00-12:00)"
            elif 12 <= hour < 17:
                return "Siang (12:00-17:00)"
            return "Sore/Malam (17:00+)"

        df["SHIFT"] = df["JAM"].apply(classify_shift)

        # Efficiency scoring
        def efficiency_score(durasi):
            if pd.isna(durasi):
                return None
            if durasi < 1:
                return "Sangat Baik"
            elif durasi < 5:
                return "Baik"
            elif durasi < 10:
                return "Cukup"
            elif durasi < 30:
                return "Lambat"
            return "Sangat Lambat"

        df["EFFICIENCY"] = df["DURASI_MENIT"].apply(efficiency_score)

        efficiency_colors = {
            "Sangat Baik": "#2ecc71",
            "Baik": "#3498db",
            "Cukup": "#f39c12",
            "Lambat": "#e74c3c",
            "Sangat Lambat": "#c0392b"
        }

        # Separate dashboard by day-of-month.
        day25_df = df[df["TANGGAL"].apply(lambda x: getattr(x, "day", None) == 25)].copy()
        day26_df = df[df["TANGGAL"].apply(lambda x: getattr(x, "day", None) == 26)].copy()

        date25, date26 = st.tabs(["📅 TANGGAL 25", "📅 TANGGAL 26"])

        with date25:
            if day25_df.empty:
                st.info("Tidak ada data untuk tanggal 25.")
            else:
                render_dashboard(day25_df, "Tanggal 25")

        with date26:
            if day26_df.empty:
                st.info("Tidak ada data untuk tanggal 26.")
            else:
                render_dashboard(day26_df, "Tanggal 26")

    except Exception as e:
        st.error(f"Terjadi error saat memproses file: {e}")
else:
    st.markdown(
        '<div class="info-box">Silakan unggah file data Excel pada sidebar '
        'untuk memulai analisis. File harus berisi kolom: WAKTU, LATITUDE, '
        'LONGITUDE, TGLBACA, IDPEL</div>',
        unsafe_allow_html=True
    )
    st.info(
        "Format file yang diharapkan:\n"
        "- WAKTU: Format duration (misal: 0 00:12:45)\n"
        "- TGLBACA: Format tanggal\n"
        "- IDPEL: ID Pelanggan\n"
        "- LATITUDE & LONGITUDE: Koordinat GPS"
    )
