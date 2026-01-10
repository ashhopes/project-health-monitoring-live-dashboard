# 1. Update everything
pip install --upgrade streamlit pandas numpy

# 2. Clear cache
rm -rf ~/.streamlit

# 3. Create and run minimal test
cat > minimal.py << 'EOF'
import streamlit as st
st.title("TEST")
st.write("If you see this, it works!")
EOF

streamlit run minimal.py --server.port=8502