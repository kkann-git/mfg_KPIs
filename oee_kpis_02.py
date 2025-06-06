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

def plot_gauge(title, value, suffix="%", alert_threshold=None, reverse_alert=False, steps=None):
    color = "darkblue"
    if alert_threshold is not None:
        if (reverse_alert and value > alert_threshold) or (not reverse_alert and value < alert_threshold):
            color = "crimson"

    if steps is None:
        # Default steps if none provided
        steps = [
            {'range': [0, 60], 'color': "#ffcccc"},
            {'range': [60, 85], 'color': "#ffe680"},
            {'range': [85, 100], 'color': "#ccffcc"},
        ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': suffix},
        title={'text': title},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': steps
        }
    ))
    st.plotly_chart(fig, use_container_width=True)

# def plot_benchmark_chart(title, values, benchmark, x_labels=None):
#     fig = go.Figure()
#     x = x_labels if x_labels is not None else list(range(1, len(values) + 1))
#     fig.add_trace(go.Scatter(x=x, y=values, mode="lines+markers", name=title))
#     # fig.add_trace(go.Bar(x=x, y=values, mode="lines+markers", name=title))
#     fig.add_trace(go.Scatter(x=x, y=[benchmark]*len(values), mode="lines", name="Benchmark", line=dict(dash="dash")))
#     fig.update_layout(title=title, xaxis_title="Description" if x_labels is not None else "Record", yaxis_title=title)
#     st.plotly_chart(fig, use_container_width=True)

def plot_benchmark_chart(title, values, benchmark, x_labels=None):
    x = x_labels if x_labels is not None else list(range(1, len(values) + 1))

    fig = go.Figure()

    # Bar chart for KPI values
    fig.add_trace(go.Bar(
        x=x,
        y=values,
        name=title,
        text=[f"{v:.1f}%" for v in values],  # Format as whole % inside bars
        textposition="inside",
        insidetextanchor="middle",
        marker_color='steelblue'
    ))

    # Line plot for benchmark
    fig.add_trace(go.Scatter(
        x=x,
        y=[benchmark] * len(values),
        mode='lines',
        name='Benchmark',
        line=dict(dash="dash", color="firebrick")        
    ))

    # Add benchmark value labels ABOVE and to the RIGHT of the line (no extra legend)
    fig.add_trace(go.Scatter(
        x=x,
        y=[benchmark]*len(values),
        mode="text",
        text=[f"{benchmark}%" for _ in values],
        textposition="top right",
        showlegend=False,  # Prevent duplicate legend item
        textfont=dict(color="firebrick", size=12)
    ))

    fig.update_layout(
        title=title,
        # xaxis_title="Description" if x_labels is not None else "Record",
        xaxis_title="Description" if x_labels else "Record",
        yaxis_title=title,
        barmode="group",
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


# def plot_benchmark_chart(title, values, benchmark, x_labels=None):
#     fig = go.Figure()

#     # Add bar chart for KPI values
#     fig.add_trace(go.Bar(
#         x = x_labels if x_labels is not None else list(range(1, len(values) + 1)),
#         y=values,
#         name=title,
#         marker_color="steelblue"
#     ))

#     # Add line for benchmark
#     fig.add_trace(go.Scatter(
#         x = x_labels if x_labels is not None else list(range(1, len(values) + 1)),
#         y=[benchmark] * len(values),
#         mode="lines",
#         name="Benchmark",
#         line=dict(color="crimson", dash="dash")
#     ))

#     # Layout settings
#     fig.update_layout(
#         title=title,
#         xaxis_title="Record" if not x_labels else "Description",
#         yaxis_title=title,
#         barmode='group',
#         template="plotly_white"
#     )

#     st.plotly_chart(fig, use_container_width=True)

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
        
        # Availability
        plot_gauge(
            "Availability",
            result["Availability"] * 100,
            suffix="%",
            alert_threshold=90,
            steps=[
                {'range': [0, 70], 'color': "#ffcccc"},
                {'range': [70, 90], 'color': "#ffe680"},
                {'range': [90, 100], 'color': "#ccffcc"}
            ]
        )
        if result["Availability"] * 100 < 90:
            st.warning("⚠️ Availability is below typical benchmark of 90%.")

        # Performance
        plot_gauge(
            "Performance",
            result["Performance"] * 100,
            suffix="%",
            alert_threshold=95,
            steps=[
                {'range': [0, 75], 'color': "#ffcccc"},
                {'range': [75, 95], 'color': "#ffe680"},
                {'range': [95, 100], 'color': "#ccffcc"}
            ]
        )    
        if result["Performance"] * 100 < 95:
            st.warning("⚠️ Performance is below typical benchmark of 95%.")
        
        # Quality
        plot_gauge(
            "Quality",
            result["Quality"] * 100,
            suffix="%",
            alert_threshold=99,
            steps=[
                {'range': [0, 90], 'color': "#ffcccc"},
                {'range': [90, 99], 'color': "#ffe680"},
                {'range': [99, 100], 'color': "#ccffcc"}
            ]
        )
        if result["Quality"] * 100 < 99:
            st.warning("⚠️ Quality is below typical benchmark of 99%.")   
        
        # OEE
        plot_gauge(
            "OEE",
            result["OEE"]*100,
            suffix="%",
            alert_threshold=85,
            steps=[
                {'range': [0, 70], 'color': "#ffcccc"},
                {'range': [70, 85], 'color': "#ffe680"},
                {'range': [85, 100], 'color': "#ccffcc"}
            ]
        )
        if result["OEE"]*100 < 85:
            st.warning("⚠️ OEE below world-class standard (85%). Consider investigating downtime, speed losses, or quality issues.")  
                
        # Scrap Rate
        plot_gauge(
            "Scrap Rate",
            result["Scrap Rate (%)"],
            suffix="%",
            alert_threshold=5,
            reverse_alert=True,
            steps=[
                {'range': [0, 2], 'color': "#ccffcc"},
                {'range': [2, 5], 'color': "#ffe680"},
                {'range': [5, 100], 'color': "#ffcccc"}
            ]
        )
        if result["Scrap Rate (%)"] > 5:
            st.warning("⚠️ Scrap Rate exceeds target of 5%. Investigate defect sources.")

        # Yield vs Planned Output
        plot_gauge(
            "Yield vs. Planned Output",
            result["Yield vs. Planned Output (%)"],
            suffix="%", 
            alert_threshold=95,
            steps=[
                {'range': [0, 70], 'color': "#ffcccc"},
                {'range': [70, 95], 'color': "#ffe680"},
                {'range': [95, 100], 'color': "#ccffcc"}
            ]
        )
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

                    # Availability
                    plot_gauge(
                        "Availability",
                        row["Availability"] * 100,
                        suffix="%",
                        alert_threshold=90,
                        steps=[
                            {'range': [0, 70], 'color': "#ffcccc"},
                            {'range': [70, 90], 'color': "#ffe680"},
                            {'range': [90, 100], 'color': "#ccffcc"}
                        ]
                    )
                    if row["Availability"] * 100 < 90:
                        st.warning("⚠️ Availability is below typical benchmark of 90%.")

                    # Performance
                    plot_gauge(
                        "Performance",
                        row["Performance"] * 100,
                        suffix="%",
                        alert_threshold=95,
                        steps=[
                            {'range': [0, 75], 'color': "#ffcccc"},
                            {'range': [75, 95], 'color': "#ffe680"},
                            {'range': [95, 100], 'color': "#ccffcc"}
                        ]
                    )
                    if row["Performance"] * 100 < 95:
                        st.warning("⚠️ Performance is below typical benchmark of 95%.")

                    # Quality
                    plot_gauge(
                        "Quality",
                        row["Quality"] * 100,
                        suffix="%",
                        alert_threshold=99,
                        steps=[
                            {'range': [0, 90], 'color': "#ffcccc"},
                            {'range': [90, 99], 'color': "#ffe680"},
                            {'range': [99, 100], 'color': "#ccffcc"}
                        ]
                    )
                    if row["Quality"] * 100 < 99:
                        st.warning("⚠️ Quality is below typical benchmark of 99%.")

                    # OEE
                    plot_gauge(
                        "OEE",
                        row["OEE"]*100,
                        suffix="%",
                        alert_threshold=85,
                        steps=[
                            {'range': [0, 70], 'color': "#ffcccc"},
                            {'range': [70, 85], 'color': "#ffe680"},
                            {'range': [85, 100], 'color': "#ccffcc"}
                        ]
                    )
                    if row["OEE"]*100 < 85:
                        st.warning("⚠️ OEE below world-class standard (85%). Consider investigating downtime, speed losses, or quality issues.")

                    # Scrap Rate
                    plot_gauge(
                        "Scrap Rate",
                        row["Scrap Rate (%)"],
                        suffix="%",
                        alert_threshold=5,
                        reverse_alert=True,
                        steps=[
                            {'range': [0, 2], 'color': "#ccffcc"},
                            {'range': [2, 5], 'color': "#ffe680"},
                            {'range': [5, 100], 'color': "#ffcccc"}
                        ]
                    )
                    if row["Scrap Rate (%)"] > 5:
                        st.warning("⚠️ Scrap Rate exceeds target of 5%. Investigate defect sources.")

                    # Yield vs Planned Output
                    plot_gauge(
                        "Yield vs. Planned Output",
                        row["Yield vs. Planned Output (%)"],
                        suffix="%", 
                        alert_threshold=95,
                        steps=[
                            {'range': [0, 70], 'color': "#ffcccc"},
                            {'range': [70, 95], 'color': "#ffe680"},
                            {'range': [95, 100], 'color': "#ccffcc"}
                        ]
                    )
                    if row["Yield vs. Planned Output (%)"] < 95:
                        st.warning("⚠️ Yield vs. Planned Output is below expected 95%. Review production efficiency.")

                else:
                    x_labels = results["Description"] if "Description" in results.columns else None
                    for metric, benchmark in zip(["Availability", "Performance", "Quality", "OEE"], [90, 95, 99, 85]):
                        # plot_benchmark_chart(f"{metric} by Machine / Process", results[metric]*100, benchmark, x_labels=x_labels)
                        plot_benchmark_chart(f"{metric} by Machine / Process", results[metric]*100, benchmark, x_labels=results["Description"])

                    # plot_benchmark_chart("Scrap Rate (%) by Machine / Process", results["Scrap Rate (%)"], 5, x_labels=x_labels)
                    # plot_benchmark_chart("Yield vs. Planned Output (%) by Machine / Process", results["Yield vs. Planned Output (%)"], 95, x_labels=x_labels)
                    plot_benchmark_chart("Scrap Rate (%) by Machine / Process", results["Scrap Rate (%)"], 5, x_labels=results["Description"])
                    plot_benchmark_chart("Yield vs. Planned Output (%) by Machine / Process", results["Yield vs. Planned Output (%)"], 95, x_labels=results["Description"])


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
