import streamlit as st
import json
from pathlib import Path
from typing import Dict, List
import re

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("CRFS Outcomes Viewer - Login")
    password_input = st.text_input("Enter password:", type="password")
    
    if st.button("Login"):
        if password_input == st.secrets["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    
    st.stop()

OUTCOME_COLORS = {
    'Knowledge Production': '#E3F2FD',
    'Development and Testing of Innovations': '#BBDEFB',
    'Improved Understanding of Climate and Food System Issues and Policy Solutions': '#90CAF9',
    'Equitable Partnerships and Networks': '#64B5F6',
    'Gender Equality and Inclusion Capacity': '#42A5F5',
    'Strengthening Diverse Southern Perspectives': '#2196F3',
    'Financial Resources Mobilized': '#1976D2',
    'Informing Policy': '#C8E6C9',
    'Informing Practice': '#A5D6A7',
    'Sustained Gender Equality and Inclusion Transformations': '#81C784',
    'Southern Voice and Leadership': '#66BB6A',
}

MARKDOWN_PATHS = {
    'LVIF_PCRs': Path('data/LVIF_PCRs'),
    'Unclassified_Cohort_PCRs_2022-2023': Path('data/Unclassified_Cohort_PCRs_2022-2023'),
    'Unclassified_Cohort_PCRs_2024-2025': Path('data/Unclassified_Cohort_PCRs_2024-2025'),
    'PCRs 2022-2023': Path('data/PCRs 2022-2023'),
    'PCRs 2024-25': Path('data/PCRs 2024-25')
}

def load_dataset(dataset_path: Path) -> List[Dict]:
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def normalize_filename(filename: str) -> str:
    name = filename.rsplit(".", 1)[0]
    name = name.replace("_", " ")
    name = name.replace("[1]", "").replace("[2]", "")
    name = re.sub(r"(PCR)(\d)", r"\1 \2", name)
    name = name.strip()
    return name + ".md"

def load_markdown_document(cohort_raw: str, filename: str, source_folder: str = None) -> str:
    base_path = MARKDOWN_PATHS.get(cohort_raw)
    
    if not base_path and source_folder:
        if '\\' in source_folder:
            folder_name = source_folder.split('\\')[-1]
        elif '/' in source_folder:
            folder_name = source_folder.split('/')[-1]
        else:
            folder_name = source_folder
            
        base_path = MARKDOWN_PATHS.get(folder_name)
    
    if not base_path:
        return None
        
    if not base_path.exists():
        return None
    
    md_filename = filename.rsplit('.', 1)[0] + '.md'
    md_path = base_path / md_filename
    
    if md_path.exists():
        with open(md_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    normalized_filename = normalize_filename(filename)
    normalized_path = base_path / normalized_filename
    
    if normalized_path.exists():
        with open(normalized_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    for md_file in base_path.glob('*.md'):
        if normalize_filename(md_file.name) == normalized_filename:
            with open(md_file, 'r', encoding='utf-8') as f:
                return f.read()
    
    return None

def highlight_quote_in_text(text: str, quote: str, color: str, quote_id: str) -> str:
    if not quote or not quote.strip():
        return text
    
    escaped_quote = re.escape(quote.strip())
    pattern = re.compile(escaped_quote, re.IGNORECASE | re.DOTALL)
    
    highlighted = pattern.sub(
        f'<mark id="{quote_id}" style="background-color: {color}; padding: 2px; border: 2px solid #FF6B00;">{quote.strip()}</mark>',
        text
    )
    return highlighted

def build_document_html(markdown_text: str, active_outcome: Dict = None) -> str:
    html_text = markdown_text.replace('\n', '<br>')
    
    if active_outcome:
        quotes = active_outcome.get('quotes', [])
        color = OUTCOME_COLORS.get(active_outcome.get('outcome_type', ''), '#FFFF00')
        
        for idx, quote in enumerate(quotes):
            quote_id = f"quote_{idx}"
            html_text = highlight_quote_in_text(html_text, quote, color, quote_id)
    
    return html_text

st.set_page_config(layout="wide", page_title="CRFS Outcomes Viewer")

st.markdown('''
<style>
[data-testid="stSidebar"] {
    overflow-y: auto;
    max-height: 100vh;
}
.main .block-container {
    overflow-y: auto;
    max-height: 100vh;
}
</style>
''', unsafe_allow_html=True)

st.title("CRFS Outcomes Dataset Viewer")

if 'selected_outcome' not in st.session_state:
    st.session_state.selected_outcome = None

dataset_path = Path("outcomes_dataset.json")

if not dataset_path.exists():
    st.error(f"Dataset not found: {dataset_path}")
    st.stop()

documents = load_dataset(dataset_path)

with st.sidebar:
    st.header("Document Selection")
    
    def normalize_cohort_name(cohort: str) -> str:
        if not cohort:
            return 'Unknown'
        if cohort == 'LVIF':
            return cohort
        if '(probable)' not in cohort:
            return f"{cohort} (probable)"
        return cohort
    
    for doc in documents:
        doc['cohort'] = normalize_cohort_name(doc.get('cohort'))
    
    all_cohorts = sorted(list(set(d['cohort'] for d in documents)))
    cohort_options = ["All"] + all_cohorts
    
    selected_cohort = st.selectbox("Filter by Cohort", options=cohort_options)
    
    batch_options = ["All", "1", "2"]
    selected_batch = st.selectbox("Filter by Batch", options=batch_options)
    
    filtered_docs = documents
    
    if selected_cohort != "All":
        filtered_docs = [d for d in filtered_docs if d['cohort'] == selected_cohort]
    
    if selected_batch != "All":
        filtered_docs = [d for d in filtered_docs if d.get('processing_batch') == selected_batch]
    
    if not filtered_docs:
        st.error(f"No documents found for cohort: {selected_cohort}")
        st.stop()
    
    selected_doc_idx = st.selectbox(
        "Select Document",
        options=range(len(filtered_docs)),
        format_func=lambda x: f"{filtered_docs[x]['project_number']} - {filtered_docs[x]['project_name'][:60]}..." 
            if filtered_docs[x]['project_name'] 
            else filtered_docs[x]['filename'][:60] + "..."
    )
    
    selected_doc = filtered_docs[selected_doc_idx]
    
    st.divider()
    st.subheader("Document Info")
    st.write(f"**Project:** {selected_doc.get('project_number', 'N/A')}")
    st.write(f"**Cohort:** {selected_doc['cohort']}")
    if selected_doc.get('cohort_confidence'):
        st.write(f"**Confidence:** {selected_doc['cohort_confidence']:.2%}")
    st.write(f"**Location:** {selected_doc.get('location_country', 'N/A')}")
    st.write(f"**Batch:** {selected_doc.get('processing_batch', 'N/A')}")
    
    if selected_doc.get('duplicate') == 1:
        st.warning("Duplicate: Batch 2 version")
    
    st.divider()
    st.subheader("Summary Statistics")
    
    total_outcomes = selected_doc['outcome_count']
    immediate_count = sum(1 for o in selected_doc['outcomes'] if o['outcome_time'] == 'immediate')
    intermediate_count = total_outcomes - immediate_count
    
    st.metric("Total Outcomes", total_outcomes)
    st.metric("Immediate", immediate_count)
    st.metric("Intermediate", intermediate_count)
    
    all_immediate_types = {
        'Knowledge Production',
        'Development and Testing of Innovations',
        'Improved Understanding of Climate and Food System Issues and Policy Solutions',
        'Equitable Partnerships and Networks',
        'Gender Equality and Inclusion Capacity',
        'Strengthening Diverse Southern Perspectives',
        'Financial Resources Mobilized'
    }
    
    all_intermediate_types = {
        'Informing Policy',
        'Informing Practice',
        'Sustained Gender Equality and Inclusion Transformations',
        'Southern Voice and Leadership'
    }
    
    found_immediate = {o['outcome_type'] for o in selected_doc['outcomes'] if o['outcome_time'] == 'immediate'}
    found_intermediate = {o['outcome_type'] for o in selected_doc['outcomes'] if o['outcome_time'] == 'intermediate'}
    
    missing_immediate = all_immediate_types - found_immediate
    missing_intermediate = all_intermediate_types - found_intermediate
    
    if missing_immediate or missing_intermediate:
        with st.expander("Missing Outcome Types", expanded=False):
            if missing_immediate:
                st.markdown("**Immediate:**")
                for outcome_type in sorted(missing_immediate):
                    st.write(f"- {outcome_type}")
            
            if missing_intermediate:
                st.markdown("**Intermediate:**")
                for outcome_type in sorted(missing_intermediate):
                    st.write(f"- {outcome_type}")
    
    st.divider()
    st.subheader("Filters")
    
    time_filter = st.multiselect(
        "Outcome Time",
        ['immediate', 'intermediate'],
        default=['immediate', 'intermediate']
    )

st.header(selected_doc.get('project_name', selected_doc['filename']))
st.caption(f"File: {selected_doc['filename']}")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Outcomes")
    
    st.markdown('''
    <style>
    .outcomes-container {
        max-height: 800px;
        overflow-y: auto;
        padding-right: 10px;
    }
    </style>
    ''', unsafe_allow_html=True)
    
    outcomes_by_type = {}
    for outcome in selected_doc['outcomes']:
        if outcome['outcome_time'] not in time_filter:
            continue
        
        outcome_key = f"{outcome['outcome_time']}_{outcome['outcome_type']}"
        
        if outcome_key not in outcomes_by_type:
            outcomes_by_type[outcome_key] = {
                'outcome_time': outcome['outcome_time'],
                'outcome_type': outcome['outcome_type'],
                'outcome': outcome
            }
    
    sorted_outcomes = sorted(
        outcomes_by_type.items(),
        key=lambda x: (x[1]['outcome_time'], x[1]['outcome_type'])
    )
    
    outcomes_container = st.container()
    with outcomes_container:
        st.markdown('<div class="outcomes-container">', unsafe_allow_html=True)
    
    for outcome_key, outcome_data in sorted_outcomes:
        outcome = outcome_data['outcome']
        outcome_time = outcome['outcome_time']
        outcome_type = outcome['outcome_type']
        
        outcome_time_label = outcome_time.title()
        color = OUTCOME_COLORS.get(outcome_type, '#FFEB3B')
        
        quote_count = len(outcome.get('quotes', []))
        button_label = f"[{outcome_time_label}] {outcome_type} ({quote_count} quotes)"
        
        if st.button(
            button_label,
            key=f"outcome_{outcome_key}",
            use_container_width=True
        ):
            st.session_state.selected_outcome = outcome
            st.rerun()
    
    with outcomes_container:
        st.markdown('</div>', unsafe_allow_html=True)
    
    if st.session_state.selected_outcome:
        outcome = st.session_state.selected_outcome
        
        st.divider()
        st.subheader(f"Selected: {outcome['outcome_type']}")
        
        with st.expander("Description", expanded=True):
            st.write(outcome['description'])
        
        if outcome.get('geography'):
            st.markdown(f"**Geography:** {outcome['geography']}")
        
        if outcome.get('target_population'):
            st.markdown(f"**Target Population:** {outcome['target_population']}")
        
        st.markdown(f"**Evidence Count:** {outcome['evidence_count']}")
        
        if outcome.get('quotes'):
            with st.expander(f"Quotes ({len(outcome['quotes'])})", expanded=False):
                for idx, quote in enumerate(outcome['quotes'], 1):
                    st.info(f"**Quote {idx}:**\n\n{quote}")

with col2:
    st.subheader("Source Document")
    
    markdown_text = load_markdown_document(
        selected_doc['cohort_raw'], 
        selected_doc['filename'],
        selected_doc.get('source_folder')
    )
    
    if markdown_text:
        active_outcome = st.session_state.selected_outcome
        
        html_content = build_document_html(markdown_text, active_outcome)
        
        if active_outcome:
            quote_count = len(active_outcome.get('quotes', []))
            st.info(f"Highlighting {quote_count} quote(s) for: {active_outcome['outcome_type']}")
        
        st.markdown(
            f'<div style="height: 800px; overflow-y: scroll; border: 1px solid #ccc; padding: 20px; background: white;">{html_content}</div>',
            unsafe_allow_html=True
        )
    else:
        st.warning(f"Source document not available for viewing.")
        st.write(f"cohort_raw: {selected_doc.get('cohort_raw', 'N/A')}")
        st.write(f"source_folder: {selected_doc.get('source_folder', 'N/A')}")
        st.write(f"filename: {selected_doc.get('filename', 'N/A')}")
        
        if selected_doc['outcomes']:
            st.subheader("Outcome Details")
            for outcome in selected_doc['outcomes']:
                if outcome['outcome_time'] not in time_filter:
                    continue
                
                with st.expander(f"{outcome['outcome_time'].title()} - {outcome['outcome_type']}"):
                    st.write(outcome['description'])
                    
                    if outcome.get('quotes'):
                        st.markdown("**Quotes:**")
                        for quote in outcome['quotes']:
                            st.info(quote)