import streamlit as st
from pypdf import PdfReader

from extraction import extract_profile
from validation import validate_profile
from fact_verification import verify_profile_facts




st.set_page_config(
    page_title="Career Assistant",
    page_icon="📄",
    layout="centered",
)

st.title("Career Assistant")
st.write(
    "Upload your CV to extract and review your profile."
)


uploaded_file = st.file_uploader(
    "Choose your CV",
    type=["pdf"],
    key="cv_upload",
)


if uploaded_file is not None:

    st.success("Your CV has been uploaded successfully!")
    st.write(f"**File:** {uploaded_file.name}")

    if st.button("Analyze CV", type="primary"):

        # Clear results from a previous analysis.
        st.session_state.pop("cv_profile", None)
        st.session_state.pop("confirmed_cv_profile", None)

        try:
            with st.spinner("Reading your CV..."):

                reader = PdfReader(uploaded_file)

                cv_text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )

            if not cv_text.strip():
                st.error(
                    "No readable text was found in this PDF. "
                    "It may be a scanned document."
                )

            else:
                st.session_state["cv_text"] = cv_text
                st.session_state["cv_filename"] = uploaded_file.name

                with st.spinner(
                    "Extracting information with AI..."
                ):
                    raw_profile = extract_profile(cv_text)

                validated_profile, errors = validate_profile(
                    raw_profile
                )

                if errors:
                    st.error(
                        "The extracted profile failed validation."
                    )
                    st.json(errors)

                else:
                    st.session_state["cv_profile"] = (
                        validated_profile
                    )

                    st.success(
                        "Information extracted successfully!"
                    )

        except Exception as error:
            st.error(
                f"CV processing failed: {error}"
            )


if "cv_profile" in st.session_state:

    st.divider()
    st.subheader("Review Your Extracted Profile")

    st.info(
        "Review the extracted information carefully. "
        "You can edit any incorrect or missing details."
    )

    profile = st.session_state["cv_profile"]

    with st.form("profile_review_form"):

        name = st.text_input(
            "Full Name",
            value=profile.get("name") or "",
        )

        email = st.text_input(
            "Email",
            value=profile.get("email") or "",
        )

        phone = st.text_input(
            "Phone",
            value=profile.get("phone") or "",
        )

        skills = st.text_area(
            "Skills — one per line",
            value="\n".join(profile.get("skills", [])),
        )

        education = st.text_area(
            "Education — one item per line",
            value="\n".join(profile.get("education", [])),
        )

        experience = st.text_area(
            "Experience — one item per line",
            value="\n".join(profile.get("experience", [])),
        )

        projects = st.text_area(
            "Projects — one item per line",
            value="\n".join(profile.get("projects", [])),
        )

        certifications = st.text_area(
            "Certifications — one item per line",
            value="\n".join(
                profile.get("certifications", [])
            ),
        )

        submitted = st.form_submit_button(
            "Validate and Confirm Profile"
        )

    if submitted:

        reviewed_profile = {
            "name": name or None,
            "email": email or None,
            "phone": phone or None,
            "skills": skills.splitlines(),
            "education": education.splitlines(),
            "experience": experience.splitlines(),
            "projects": projects.splitlines(),
            "certifications": certifications.splitlines(),
        }

        validated_profile, errors = validate_profile(
            reviewed_profile
        )

        if errors:
            st.error(
                "Some fields are invalid. Please correct them."
            )
            st.json(errors)

        else:
            st.session_state["confirmed_cv_profile"] = (
                validated_profile
            )

            st.success(
                "Your profile has been confirmed for this session."
            )

            st.subheader("Confirmed Profile")
            st.json(validated_profile)

            st.caption(
                "The profile is currently stored in the session "
                "only. It has not been saved to a database."
            )

if st.button("Verify Profile Facts", type="secondary"):

    if "confirmed_cv_profile" not in st.session_state:
        st.warning(
            "Please validate and confirm your profile first."
        )

    else:
        try:
            with st.spinner(
                "Checking extracted facts against your CV..."
            ):
                verification = verify_profile_facts(
                    st.session_state["cv_text"],
                    st.session_state["confirmed_cv_profile"],
                )

                st.session_state["cv_verification"] = verification

        except Exception as error:
            st.error(f"Fact verification failed: {error}")


if "cv_verification" in st.session_state:

    st.subheader("Fact Verification Results")

    results = st.session_state["cv_verification"]["results"]

    for item in results:

        status = item.get("status", "needs_review")

        if status == "supported":
            st.success(f"Supported: {item.get('claim', '')}")

        elif status == "not_found":
            st.error(f"Not found: {item.get('claim', '')}")

        else:
            st.warning(f"Needs review: {item.get('claim', '')}")

        st.write(f"**Field:** {item.get('field', '')}")
        st.write(
            f"**Evidence:** "
            f"{item.get('evidence') or 'No evidence provided'}"
        )
        st.write(f"**Reason:** {item.get('reason', '')}")
        st.write(
            f"**Evidence check:** "
            f"{item.get('evidence_check', 'not checked')}"
        )

        st.divider()