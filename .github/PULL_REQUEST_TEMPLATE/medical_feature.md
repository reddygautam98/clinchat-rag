---
name: 🏥 Medical Feature Pull Request
about: New medical functionality, clinical algorithms, or patient-facing features
title: 'feat(scope): '
labels: ['feature', 'medical', 'needs-clinical-review']
---

## 🏥 Medical Feature Description
<!-- Describe the medical functionality being added -->

**Clinical Use Case:**
<!-- What medical problem does this solve? Which clinical workflows are improved? -->

**Medical Domain:**
<!-- e.g., Cardiology, Oncology, Pharmacy, Diagnostics, etc. -->

**Feature Type:**
- [ ] Clinical decision support
- [ ] Medical data processing  
- [ ] Patient safety feature
- [ ] Diagnostic assistance
- [ ] Drug interaction checking
- [ ] Clinical documentation
- [ ] Medical imaging analysis
- [ ] Laboratory result interpretation
- [ ] Other: _______________

## 🧪 Clinical Validation

**Medical Accuracy Testing:**
- [ ] Validated against medical literature/guidelines
- [ ] Tested with synthetic clinical scenarios
- [ ] Reviewed clinical edge cases
- [ ] Cross-referenced with medical databases

**Clinical Evidence:**
<!-- Link to medical studies, guidelines, or clinical protocols supporting this feature -->

**Medical Review Status:**
- [ ] Pending medical professional review
- [ ] Reviewed by medical professional
- [ ] Approved by medical director
- [ ] Clinical validation completed

**Reviewer:** 
<!-- Medical professional who reviewed this change -->

## 🔄 Technical Changes

**Files Modified:**
<!-- List key files changed, especially medical algorithms -->

**API Changes:**
- [ ] New medical endpoints added
- [ ] Existing medical APIs modified
- [ ] Breaking changes to clinical interfaces
- [ ] No API changes

**Database Schema:**
- [ ] New medical data tables
- [ ] Modified patient data fields
- [ ] Added clinical indices
- [ ] No database changes

## 🧪 Testing & Validation

**Automated Tests:**
- [ ] Unit tests for medical logic
- [ ] Integration tests with clinical data
- [ ] API endpoint tests
- [ ] End-to-end clinical workflow tests

**Manual Testing:**
- [ ] Tested with medical test cases
- [ ] Validated clinical accuracy
- [ ] Tested edge cases and error handling
- [ ] Performance testing with medical datasets

**Test Coverage:**
- Medical logic: __%
- Clinical workflows: __%
- Overall: __%

## 🔒 Security & Compliance

**HIPAA Compliance:**
- [ ] No PHI (Protected Health Information) exposed
- [ ] Proper data encryption for medical data
- [ ] Audit logging for clinical actions
- [ ] Access controls for medical features
- [ ] Data retention policies followed

**Medical Data Security:**
- [ ] Patient data properly anonymized/de-identified
- [ ] Medical records access logged
- [ ] Encryption at rest and in transit
- [ ] Secure medical data transmission

**Privacy Impact:**
- [ ] No new patient data collection
- [ ] New patient data collection (describe below)
- [ ] Changes to data processing (describe below)

## 📋 Clinical Documentation

**Medical Algorithms:**
<!-- Describe any new clinical algorithms, decision trees, or medical logic -->

**Clinical References:**
<!-- List medical literature, guidelines, or protocols referenced -->

**Medical Disclaimers:**
- [ ] Added appropriate medical disclaimers
- [ ] Clarified clinical decision support vs. diagnosis
- [ ] Documented limitations and contraindications

## 🚀 Deployment Considerations

**Clinical Impact:**
- [ ] Low impact - administrative feature
- [ ] Medium impact - affects clinical workflows
- [ ] High impact - critical medical functionality
- [ ] Emergency - urgent medical fix

**Rollout Strategy:**
- [ ] Gradual rollout to select clinicians
- [ ] Full deployment to all medical users
- [ ] Feature flag controlled release
- [ ] Requires maintenance window

**Training Requirements:**
- [ ] No additional training needed
- [ ] Brief user notification required
- [ ] Full clinical training program needed
- [ ] Medical staff orientation required

## ✅ Pre-Merge Checklist

### Medical Requirements:
- [ ] Clinical accuracy validated
- [ ] Medical professional review completed
- [ ] Medical disclaimers and limitations documented
- [ ] Clinical test scenarios passed
- [ ] Medical literature references provided

### Technical Requirements:
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code review completed
- [ ] Security review completed (if applicable)
- [ ] Performance benchmarks met
- [ ] Documentation updated

### Compliance Requirements:
- [ ] HIPAA compliance verified
- [ ] Patient privacy protected
- [ ] Audit requirements met
- [ ] Data security validated
- [ ] Medical device regulations considered (if applicable)

### Quality Assurance:
- [ ] Medical QA testing completed
- [ ] User acceptance testing with clinical staff
- [ ] Accessibility requirements met
- [ ] Browser compatibility tested
- [ ] Mobile responsiveness verified (if applicable)

## 🏥 Medical Sign-off

**Clinical Reviewer:** <!-- Name and credentials -->
**Review Date:** <!-- Date -->
**Medical Approval:** <!-- Approved/Pending/Rejected -->

**Clinical Notes:**
<!-- Any specific clinical considerations or recommendations -->

## 📝 Additional Notes

<!-- Any other relevant information for reviewers -->

**Related Issues:**
<!-- Link related issues: Fixes #123, Relates to #456 -->

**Dependencies:**
<!-- Any dependencies on other PRs or external systems -->

**Breaking Changes:**
<!-- Describe any breaking changes that affect clinical workflows -->

---

**⚠️ Medical Disclaimer:** This system provides clinical decision support and should not replace professional medical judgment. All medical features require appropriate clinical validation and professional oversight.