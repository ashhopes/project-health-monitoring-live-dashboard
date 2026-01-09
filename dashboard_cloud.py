# ============ TAB 3: ANALYTICS & TRENDS ============
with tab3:
    st.header(f"Analytics & Trends - Node: {selected_node}")
    
    if node_df.empty:
        st.warning(f"📭 No analytics data available for node {selected_node}")
    else:
        # CLEAN THE DATA FIRST - THIS IS THE KEY FIX
        # Create a clean copy for analytics
        analytics_df = node_df.copy()
        
        # Fill NaN values in numeric columns with safe defaults
        numeric_cols = ['hr', 'spo2', 'temp', 'ax', 'ay', 'az', 'gx', 'gy', 'gz']
        for col in numeric_cols:
            if col in analytics_df.columns:
                if col == 'hr':
                    analytics_df[col] = analytics_df[col].fillna(72)  # Normal HR
                elif col == 'spo2':
                    analytics_df[col] = analytics_df[col].fillna(98)  # Normal SpO2
                elif col == 'temp':
                    analytics_df[col] = analytics_df[col].fillna(36.5)  # Normal temp
                else:
                    analytics_df[col] = analytics_df[col].fillna(0)  # Motion data
        
        # Now use analytics_df for all calculations instead of node_df
        # ... rest of your code using analytics_df ...