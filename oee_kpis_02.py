import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page title and layout
st.set_page_config(page_title="OEE Calculator", layout="centered")

st.title("📊 OEE & Manufacturing KPIs Dashboard")
st.markdown("""
This tool calculates **OEE**, **Scrap Rate**, and **Yield vs. Planned Output** from your production data.
Upload a CSV or enter data manually to see KPIs, benchmarks, and alerts.
""")

st.info("PLEASE NOTE: Entered data will only be stored in memory (RAM) only for the duration of the session and is deleted as soon as it is no longer needed—such as when the user uploads another file, clears the file uploader, or closes the browser tab. This data is not saved to disk or permanently stored in this app.")

input_method = st.radio("Select input method:", ["Manual Entry", "Upload CSV"])

def calculate_kpis(df):
    df["Run Time"] = df["Planned Production Time"] - df["Downtime"]
    df["Availability"] = df["Run Time"] / df["Planned Production Time"]
    df["Performance"] = (df["Ideal Cycle Time"] * df["Total Count"]) / df["Run Time"]
    df["Quality"] = df["Good Count"] / df["Total Count"]
    df["OEE"] = df["Availability"] * df["Performance"] * df["Quality"]

    df["Scrap Count"] = df["Total Count"] - df["Good Count"]
    df["Scrap Rate (%)"] = (df["Scrap Count"] / df["Total Count"]) * 100
    df["Planned Output"] = df["Planned Production Time"] / df["Ideal Cycle Time"]
    df["Yield vs. Planned Output (%)"] = (df["Good Count"] / df["Planned Output"]) * 100
    return df

def plot_gauge(title, value, suffix="%", alert_threshold=None, reverse_alert=False):
    color = "darkblue"
    if alert_threshold is not None:
        if (reverse_alert and value > alert_threshold) or (not reverse_alert and value < alert_threshold):
            color = "crimson"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': suffix},
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': "#ffcccc"},
                {'range': [60, 85], 'color': "#ffe680"},
                {'range': [85, 100], 'color': "#ccffcc"},
            ]
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

def plot_benchmark_chart(title, values, benchmark, x_labels=None):
    fig = go.Figure()
    x = x_labels if x_labels is not None else list(range(1, len(values) + 1))
    fig.add_trace(go.Scatter(x=x, y=values, mode="lines+markers", name=title))
    fig.add_trace(go.Scatter(x=x, y=[benchmark]*len(values), mode="lines", name="Benchmark", line=dict(dash="dash")))
    fig.update_layout(title=title, xaxis_title="Description" if x_labels is not None else "Record", yaxis_title=title)
    st.plotly_chart(fig, use_container_width=True)

if input_method == "Manual Entry":
    with st.form("manual_kpis"):
        st.subheader("🔧 Input Production Data")
        description = st.text_input("Description (Machine/Process)")
        planned_production_time = st.number_input("Planned Production Time (minutes)", min_value=1.0)
        downtime = st.number_input("Unplanned Downtime (minutes)", min_value=0.0)
        total_count = st.number_input("Total Units Produced", min_value=1)
        good_count = st.number_input("Good Units Produced", min_value=0, max_value=total_count)
        ideal_cycle_time = st.number_input("Ideal Cycle Time per Unit (minutes)", min_value=0.01)
        submitted = st.form_submit_button("Calculate KPIs")

    if submitted:
        df = pd.DataFrame({
            "Description": [description],
            "Planned Production Time": [planned_production_time],
            "Downtime": [downtime],
            "Total Count": [total_count],
            "Good Count": [good_count],
            "Ideal Cycle Time": [ideal_cycle_time]
        })
        result = calculate_kpis(df).iloc[0]

        st.success("✅ KPIs Calculated")
        for kpi, label, threshold in zip(["Availability", "Performance", "Quality"],
                                         ["Availability", "Performance", "Quality"], [90, 95, 99]):
            plot_gauge(label, result[kpi]*100, suffix="%", alert_threshold=threshold)
            if result[kpi]*100 < threshold:
                st.warning(f"⚠️ {label} is below typical benchmark of {threshold}%.")

        plot_gauge("OEE", result["OEE"]*100, suffix="%", alert_threshold=85)
        if result["OEE"]*100 < 85:
            st.warning("⚠️ OEE below world-class standard (85%). Consider investigating downtime, speed losses, or quality issues.")

        plot_gauge("Scrap Rate", result["Scrap Rate (%)"], suffix="%", alert_threshold=5, reverse_alert=True)
        if result["Scrap Rate (%)"] > 5:
            st.warning("⚠️ Scrap Rate exceeds target of 5%. Investigate defect sources.")

        plot_gauge("Yield vs. Planned Output", result["Yield vs. Planned Output (%)"], suffix="%", alert_threshold=95)
        if result["Yield vs. Planned Output (%)"] < 95:
            st.warning("⚠️ Yield vs. Planned Output is below expected 95%. Review production efficiency.")

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Input Data (CSV)", csv, "input_data.csv", "text/csv")

else:
    st.subheader("📂 Upload CSV File")
    uploaded_file = st.file_uploader("Upload CSV", type="csv")

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)
            required_cols = ["Planned Production Time", "Downtime", "Total Count", "Good Count", "Ideal Cycle Time"]
            if not all(col in df.columns for col in required_cols):
                st.error("❌ CSV is missing required columns.")
            else:
                results = calculate_kpis(df)
                st.success("✅ KPIs Calculated for All Records")
                st.dataframe(results[[
                    "Description", "Planned Production Time", "Downtime", "Total Count", "Good Count",
                    "Availability", "Performance", "Quality", "OEE",
                    "Scrap Rate (%)", "Yield vs. Planned Output (%)"]])

                if len(results) == 1:
                    row = results.iloc[0]
                    for kpi, label, threshold in zip(["Availability", "Performance", "Quality"],
                                                     ["Availability", "Performance", "Quality"], [90, 95, 99]):
                        plot_gauge(label, row[kpi]*100, suffix="%", alert_threshold=threshold)
                        if row[kpi]*100 < threshold:
                            st.warning(f"⚠️ {label} is below typical benchmark of {threshold}%.")

                    plot_gauge("OEE", row["OEE"]*100, suffix="%", alert_threshold=85)
                    if row["OEE"]*100 < 85:
                        st.warning("⚠️ OEE below world-class standard (85%). Consider investigating downtime, speed losses, or quality issues.")

                    plot_gauge("Scrap Rate", row["Scrap Rate (%)"], suffix="%", alert_threshold=5, reverse_alert=True)
                    if row["Scrap Rate (%)"] > 5:
                        st.warning("⚠️ Scrap Rate exceeds target of 5%. Investigate defect sources.")

                    plot_gauge("Yield vs. Planned Output", row["Yield vs. Planned Output (%)"], suffix="%", alert_threshold=95)
                    if row["Yield vs. Planned Output (%)"] < 95:
                        st.warning("⚠️ Yield vs. Planned Output is below expected 95%. Review production efficiency.")

                else:
                    x_labels = results["Description"] if "Description" in results.columns else None
                    for metric, benchmark in zip(["Availability", "Performance", "Quality", "OEE"], [90, 95, 99, 85]):
                        plot_benchmark_chart(f"{metric} Over Time", results[metric]*100, benchmark, x_labels=x_labels)

                    plot_benchmark_chart("Scrap Rate (%) Over Time", results["Scrap Rate (%)"], 5, x_labels=x_labels)
                    plot_benchmark_chart("Yield vs. Planned Output (%) Over Time", results["Yield vs. Planned Output (%)"], 95, x_labels=x_labels)

                export_csv = results.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Download Results (CSV)", export_csv, "kpi_results.csv", "text/csv")

                # Buy Me a Coffee
                st.markdown("""
                    <div style="text-align: center; margin-top: 2em;">
                        <a href="https://www.buymeacoffee.com/kkann" target="_blank">
                            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-orange.png" 
                                alt="Buy Me A Coffee" 
                                style="height: 60px !important;width: 217px !important;">
                        </a>
                    </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"An error occurred: {e}")
