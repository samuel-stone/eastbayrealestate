with tab_business:
    st.subheader("📄 Client Prospecting & Property Valuation Architect")
    st.markdown("Generate client-ready real estate listing proposals, Rossmoor market briefs, and property value-add summaries.")

    col1, col2 = st.columns(2)
    with col1:
        target_city_input = st.text_input("Target Municipality / Neighborhood", value="Walnut Creek")
    with col2:
        client_focus_input = st.selectbox("Prospecting Focus", [
            "Rossmoor & Senior Living Infill",
            "ADU & Infill Development Potential",
            "Standard Listing & Staging Proposal",
            "Buyer Investment Analysis"
        ])
    
    if st.button("Generate Client Prospecting Document"):
        with st.spinner("Drafting client-ready real estate proposal..."):
            proposal_text, proposal_source = business_proposal_architect.generate_business_proposal(
                target_city=target_city_input,
                client_focus=client_focus_input
            )
            
        st.success(f"Proposal successfully drafted!")
        st.markdown(proposal_text)
        
        st.download_button(
            label="📥 Download Client Proposal (.md)",
            data=proposal_text,
            file_name=f"property_proposal_{target_city_input.lower().replace(' ', '_')}.md",
            mime="text/markdown"
        )