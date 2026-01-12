Update dashboard_cloud.py
82a6e41
dashboard_cloud.py
        - Project ID: {PROJECT_ID}
        - Dataset: {DATASET_ID}
        - Table: {TABLE_ID}
        - Table Columns: {table_columns}
        - Selected User: {selected_user}
        - Time Filter: {hours_filter} hours
        - Sample Size: {n_samples}
        """)
    
    st.markdown("""
    ### 🚨 Immediate Actions:
    1. **Check your batch file** is running and uploading data
    2. **Verify BigQuery table** has the expected columns
    3. **Adjust time filter** to see older data
    4. **Try selecting "All Users"** in sidebar
    5. **Check your uploader script** for column names
    """)

if __name__ == "__main__":
    # Command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "test":
            test_parsers()
        elif command == "check":
            check_bigquery_data()
        elif command == "help":
            print("Usage:")
            print("  python lora_uploader_fixed.py          # Run uploader")
            print("  python lora_uploader_fixed.py test     # Test parsers")
            print("  python lora_uploader_fixed.py check    # Check BigQuery data")
        else:
            print(f"Unknown command: {command}")
            print("Use: test, check, or help")
    else:
        # Run the main uploader
        main()
# --- Footer ---
st.markdown("---")
st.markdown("<div style='text-align: center; color: #666; font-size: 0.9em;'>", unsafe_allow_html=True)
st.markdown("🏥 **STEMCUBE Health Monitoring System** | 📡 **LoRa Technology** | 🎓 **UMP Final Year Project 2024**")
st.markdown("</div>", unsafe_allow_html=True)