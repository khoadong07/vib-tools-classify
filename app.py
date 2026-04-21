import streamlit as st
import pandas as pd
import json
from io import BytesIO
from main import process_text_full, load_class_labels

# Page configuration
st.set_page_config(
    page_title="VIB Credit Card Classifier",
    layout="wide"
)

# Load class labels
@st.cache_resource
def load_labels():
    return load_class_labels("class.json")

def merge_text_columns(row):
    """Merge Title, Content, Description columns into one text"""
    parts = []
    if pd.notna(row.get('Title')):
        parts.append(str(row['Title']))
    if pd.notna(row.get('Content')):
        parts.append(str(row['Content']))
    if pd.notna(row.get('Description')):
        parts.append(str(row['Description']))
    return ' '.join(parts)

def process_excel(df, class_labels):
    """Process DataFrame and add Labels columns"""
    # Merge text
    df['merged_text'] = df.apply(merge_text_columns, axis=1)
    
    # Initialize Labels columns
    df['Labels1'] = None
    df['Labels2'] = None
    df['Labels3'] = None
    df['Labels4'] = None
    
    # Process each row
    progress_bar = st.progress(0)
    for idx, row in df.iterrows():
        result = process_text_full(row['merged_text'], class_labels)
        
        df.at[idx, 'Labels1'] = result['Labels1']
        df.at[idx, 'Labels2'] = result['Labels2']
        df.at[idx, 'Labels3'] = result['Labels3']
        df.at[idx, 'Labels4'] = result['Labels4']
        
        progress_bar.progress((idx + 1) / len(df))
    
    progress_bar.empty()
    return df

def main():
    st.title("VIB Credit Card Text Classifier")
    st.markdown("Upload Excel file for automatic classification and labeling")
    
    # Sidebar
    with st.sidebar:
        st.header("Instructions")
        st.markdown("""
        1. Upload Excel file (.xlsx or .xls)
        2. File should contain columns: Title, Content, Description
        3. System will merge text and classify
        4. Results include 4 labels:
           - Labels1: CREDIT CARD
           - Labels2: Specific card type
           - Labels3: Topic
           - Labels4: Details
        5. Download result file
        """)
    
    # Upload file
    uploaded_file = st.file_uploader(
        "Select Excel file",
        type=['xlsx', 'xls'],
        help="Excel file should contain columns: Title, Content, Description"
    )
    
    if uploaded_file:
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file)
            
            st.success(f"File loaded: {uploaded_file.name}")
            st.info(f"Number of rows: {len(df)}")
            
            # Display preview
            with st.expander("View original data"):
                st.dataframe(df.head(10))
            
            # Check required columns
            required_cols = ['Title', 'Content', 'Description']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.warning(f"Missing columns: {', '.join(missing_cols)}")
                st.info("System will process with available columns")
            
            # Process button
            if st.button("Start Processing", type="primary"):
                with st.spinner("Processing..."):
                    class_labels = load_labels()
                    result_df = process_excel(df.copy(), class_labels)
                
                st.success("Processing completed!")
                
                # Display results
                st.subheader("Classification Results")
                
                # Statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    count_l1 = result_df['Labels1'].notna().sum()
                    st.metric("Labels1", count_l1)
                with col2:
                    count_l2 = result_df['Labels2'].notna().sum()
                    st.metric("Labels2", count_l2)
                with col3:
                    count_l3 = result_df['Labels3'].notna().sum()
                    st.metric("Labels3", count_l3)
                with col4:
                    count_l4 = result_df['Labels4'].notna().sum()
                    st.metric("Labels4", count_l4)
                
                # Display result table
                st.dataframe(result_df)
                
                # Download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False, sheet_name='Results')
                output.seek(0)
                
                st.download_button(
                    label="Download Results",
                    data=output,
                    file_name=f"classified_{uploaded_file.name}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()
