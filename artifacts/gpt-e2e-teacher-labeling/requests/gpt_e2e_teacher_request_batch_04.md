# GPT End-to-End Health-Agent Teacher Label Request

Return JSONL only, one JSON object per patient. Do not wrap in markdown.

## System Instructions

You are a GPT teacher labeler creating end-to-end answer keys for a clinical-trial matching multi-agent workflow.

Use only the synthetic patient information and candidate trial information provided in the input file. Do not use outside medical knowledge to add unstated patient facts.
This is for software evaluation only, not medical advice.

For every patient, produce exactly one JSON object.
Return JSONL only. No markdown, no commentary.

Required workflow represented in each output object:
1. criteria_parser_agent: convert trial inclusion/exclusion criteria into structured rules.
2. patient_information_understanding_agent: extract the patient profile from the patient information string.
3. inference_matching_agent: judge criterion-level satisfaction for each candidate trial using currently known patient information.
4. question_generation_agent: generate follow-up questions for missing required facts.
5. interaction_simulation_agent: provide synthetic patient answers to the generated questions.
6. recommendation_agent: rank the candidate trials for the patient after applying the synthetic answers.
7. result_explanation_agent: explain final judgment and recommendations.

Allowed trial-level eligibility labels: eligible, ineligible, uncertain.
Allowed criterion status labels: satisfied, violated, unknown, not_applicable.

For exclusion criteria: satisfied means the exclusion is absent; violated means the exclusion is present.
If a required fact is missing, mark that criterion unknown, generate a question, then create a plausible synthetic answer. The final recommendation should reflect the answer.
Every candidate trial must appear exactly once in final_output.recommendations.
Every supplied criterion_id for a candidate trial must appear exactly once in initial and final criterion_results.


## Required Output Schema

```json
{
  "patient_id": "same patient_id",
  "input": {
    "patient_information_string": "same supplied patient string",
    "candidate_trial_ids": [
      "trial ids in supplied order"
    ]
  },
  "agent_trace": {
    "criteria_parser_agent": {
      "parsed_trials": [
        {
          "trial_id": "trial id",
          "structured_rules": [
            {
              "criterion_id": "same supplied criterion_id",
              "criterion_type": "inclusion|exclusion",
              "criterion": "short parsed criterion",
              "required": true
            }
          ]
        }
      ]
    },
    "patient_information_understanding_agent": {
      "extracted_profile": {
        "age": "number or null",
        "sex": "string or null",
        "diagnosis": "string or null",
        "stage": "string or null",
        "ecog": "number or null",
        "biomarkers": {},
        "prior_treatments": [],
        "flags": {}
      },
      "missing_or_unstated_fields": [
        "field names"
      ]
    },
    "inference_matching_agent": {
      "initial_trial_judgments": [
        {
          "trial_id": "trial id",
          "eligibility": "eligible|ineligible|uncertain",
          "criterion_results": [
            {
              "criterion_id": "same supplied criterion_id",
              "status": "satisfied|violated|unknown|not_applicable",
              "reason": "grounded reason"
            }
          ],
          "rationale": "short reason"
        }
      ]
    },
    "question_generation_agent": {
      "questions": [
        {
          "question_id": "patient_id__trial_id__Q01",
          "patient_id": "patient id",
          "trial_id": "trial id",
          "criterion_id": "criterion id",
          "question": "follow-up question",
          "reason": "why this information is needed"
        }
      ]
    },
    "interaction_simulation_agent": {
      "simulated_patient_answers": [
        {
          "question_id": "same question id",
          "answer": "synthetic patient answer",
          "profile_updates": {}
        }
      ]
    },
    "recommendation_agent": {
      "recommended_trial_order": [
        "trial ids ordered best to worst"
      ],
      "ranked_recommendations": [
        {
          "rank": 1,
          "trial_id": "trial id",
          "eligibility": "eligible|ineligible|uncertain",
          "recommendation_score": 0.0
        }
      ]
    },
    "result_explanation_agent": {
      "summary": "plain-language explanation",
      "medical_disclaimer": "software evaluation only, not medical advice"
    }
  },
  "final_output": {
    "patient_id": "same patient_id",
    "recommendations": [
      {
        "rank": 1,
        "trial_id": "trial id",
        "trial_title": "trial title",
        "eligibility": "eligible|ineligible|uncertain",
        "criterion_results": [
          {
            "criterion_id": "same supplied criterion_id",
            "status": "satisfied|violated|unknown|not_applicable",
            "reason": "grounded reason after simulated answers"
          }
        ],
        "follow_up_questions": [],
        "simulated_patient_answers": [],
        "explanation": "why this final judgment and rank were assigned"
      }
    ],
    "recommended_trial_order": [
      "trial ids ordered best to worst"
    ],
    "medical_disclaimer": "software evaluation only, not medical advice"
  }
}
```

## Input Batch

{
  "batch_id": "gpt_e2e_teacher_batch_04",
  "patients": [
    {
      "patient_id": "SYN-GEN-00016",
      "patient_information_string": "Tumor board intake: SYN-GEN-00016 is a 48-year-old female with graves disease. Stage is recorded as III. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in IL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00016",
        "age": 48,
        "sex": "female",
        "diagnosis": "graves disease",
        "stage": "III",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "IL"
        },
        "scenario": "prior_treatment_gap",
        "target_trial_id": "NCT06963203"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT06963203",
          "title": "Thyroidectomy for Graves' Disease or Amiodarone-induced Thyrotoxicosis",
          "source_url": "https://clinicaltrials.gov/study/NCT06963203",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Graves Disease",
            "Amiodarone-Induced Thyrotoxicosis",
            "Thyroidectomy"
          ],
          "phase": null,
          "status": "RECRUITING",
          "interventions": [],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06963203-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Graves Disease",
                "Amiodarone-Induced Thyrotoxicosis",
                "Thyroidectomy"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06963203-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Adult patients (>= 18 years of age) undergoing surgical treatment for Graves' disease or Amiodarone-induced thyrotoxicosis (AIT) with biochemically confirmed hyperthyroidism or on specific medication for the treatment of Graves' disease or AIT.",
              "Patients providing signed informed consent."
            ],
            "exclusion": [
              "Children and minors (\\<18 years).",
              "Pregnant women.",
              "Patients unable or unwilling to provide informed consent due to language barriers or intellectual limitations.",
              "Patients undergoing concurrent parathyroidectomy for primary or secondary hyperparathyroidism, lymph node clearance, or redo surgery.",
              "Surgical procedures performed for other reasons than Graves' disease or AIT"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Adult patients (>= 18 years of age) undergoing surgical treatment for Graves' disease or Amiodarone-induced thyrotoxicosis (AIT) with biochemically confirmed hyperthyroidism or on specific medication for the treatment of Graves' disease or AIT. * Patients providing signed informed consent. Exclusion Criteria: * Children and minors (\\<18 years). * Pregnant women. * Patients unable or unwilling to provide informed consent due to language barriers or intellectual limitations. * Patients undergoing concurrent parathyroidectomy for primary or secondary hyperparathyroidism, lymph node clearance, or redo surgery. * Surgical procedures performed for other reasons than Graves' disease or AIT"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 302.18,
          "conditions": [
            "Locally Advanced Bladder Urothelial Carcinoma",
            "Locally Advanced Renal Pelvis Urothelial Carcinoma",
            "Locally Advanced Ureter Urothelial Carcinoma",
            "Locally Advanced Urethral Urothelial Carcinoma",
            "Metastatic Bladder Urothelial Carcinoma",
            "Metastatic Renal Pelvis Urothelial Carcinoma",
            "Metastatic Ureter Urothelial Carcinoma",
            "Metastatic Urethral Urothelial Carcinoma",
            "Recurrent Bladder Urothelial Carcinoma",
            "Recurrent Renal Pelvis Urothelial Carcinoma",
            "Recurrent Ureter Urothelial Carcinoma",
            "Recurrent Urethral Urothelial Carcinoma",
            "Stage III Bladder Cancer AJCC v8",
            "Stage III Renal Pelvis Cancer AJCC v8",
            "Stage III Ureter Cancer AJCC v8",
            "Stage III Urethral Cancer AJCC v8",
            "Stage IV Bladder Cancer AJCC v8",
            "Stage IV Renal Pelvis Cancer AJCC v8",
            "Stage IV Ureter Cancer AJCC v8",
            "Stage IV Urethral Cancer AJCC v8",
            "Unresectable Bladder Urothelial Carcinoma",
            "Unresectable Renal Pelvis Urothelial Carcinoma",
            "Unresectable Ureter Urothelial Carcinoma",
            "Unresectable Urethral Urothelial Carcinoma"
          ],
          "phase": "PHASE2",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Atezolizumab",
            "Biopsy Procedure",
            "Biospecimen Collection",
            "Computed Tomography with Contrast",
            "Eribulin Mesylate"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 2,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03237780-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Locally Advanced Bladder Urothelial Carcinoma",
                "Locally Advanced Renal Pelvis Urothelial Carcinoma",
                "Locally Advanced Ureter Urothelial Carcinoma",
                "Locally Advanced Urethral Urothelial Carcinoma",
                "Metastatic Bladder Urothelial Carcinoma",
                "Metastatic Renal Pelvis Urothelial Carcinoma",
                "Metastatic Ureter Urothelial Carcinoma",
                "Metastatic Urethral Urothelial Carcinoma",
                "Recurrent Bladder Urothelial Carcinoma",
                "Recurrent Renal Pelvis Urothelial Carcinoma",
                "Recurrent Ureter Urothelial Carcinoma",
                "Recurrent Urethral Urothelial Carcinoma",
                "Stage III Bladder Cancer AJCC v8",
                "Stage III Renal Pelvis Cancer AJCC v8",
                "Stage III Ureter Cancer AJCC v8",
                "Stage III Urethral Cancer AJCC v8",
                "Stage IV Bladder Cancer AJCC v8",
                "Stage IV Renal Pelvis Cancer AJCC v8",
                "Stage IV Ureter Cancer AJCC v8",
                "Stage IV Urethral Cancer AJCC v8",
                "Unresectable Bladder Urothelial Carcinoma",
                "Unresectable Renal Pelvis Urothelial Carcinoma",
                "Unresectable Ureter Urothelial Carcinoma",
                "Unresectable Urethral Urothelial Carcinoma"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 2,
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study",
              "Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra",
              "Presence of measurable disease meeting the following criteria:",
              "At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm",
              "Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion",
              "Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence",
              "PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to allow for stratification; COMMERCIAL ASSESSMENT OF PD-L1 STATUS OBTAINED LOCALLY AT THE SITE WILL NOT SATISFY ELIGIBILITY CRITERIA",
              "New, progressive or recurrent disease occurring",
              "During or within 12 months of treatment with a platinum containing regimen (cisplatin or carboplatin or novel platinum) in either in the metastatic or perioperative setting",
              "In first-line patients defined as cisplatin-ineligible based on renal impairment (creatinine clearance calculated by Cockcroft-Gault method \\< 60 ml/min), at least grade 2 hearing loss and/or Eastern Cooperative Oncology Group (ECOG) status of 2; these patients will be chemotherapy naive or have received platinum based therapy in the adjuvant or neoadjuvant setting more than 12 months prior to study entry"
            ],
            "exclusion": [
              "Patients with prior allogeneic bone marrow transplantation or prior solid organ transplantation",
              "Patients who have had chemotherapy within 3 weeks or radiotherapy or targeted therapy 2 weeks (6 weeks for nitrosoureas or mitomycin C) prior to entering the study or those who have not recovered from adverse events (other than alopecia) due to agents administered more than 4 weeks earlier; however, the following therapies are allowed:",
              "Hormone-replacement therapy or oral contraceptives",
              "Herbal therapy \\> 1 week prior to cycle 1, day 1 (herbal therapy intended as anticancer therapy must be discontinued at least 1 week prior to cycle 1, day 1)",
              "Palliative radiotherapy for bone metastases \\> 2 weeks prior to cycle 1, day 1",
              "Prior treatment with anti-PD-1, or anti-PD-L1 therapeutic antibody or pathway-targeting agents or eribulin",
              "Patients who have received prior treatment with anti-CTLA-4 may be enrolled, provided the following requirements are met:",
              "Minimum of 12 weeks from the first dose of anti-CTLA-4 and \\> 6 weeks from the last dose",
              "No history of severe immune-related adverse effects from anti-CTLA-4 (National Cancer Institute \\[NCI\\] Common Terminology Criteria for Adverse Events \\[CTCAE\\] version 5.0)",
              "Treatment with any other investigational agent within 4 weeks prior to cycle 1, day 1"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study * Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra * Presence of measurable disease meeting the following criteria: * At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm * Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion * Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence * PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 3,
          "retrieval_score": 246.413,
          "conditions": [
            "Urothelial Cancer",
            "Metastatic Urothelial Carcinoma",
            "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
            "Bladder Cancer"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Sacituzumab Govitecan (SG)",
            "Enfortumab vedotin-ejfv (EV)",
            "Pembrolizumab"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04724018-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Urothelial Cancer",
                "Metastatic Urothelial Carcinoma",
                "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
                "Bladder Cancer"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination)",
              "Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible.",
              "Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor.",
              "Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease",
              "Patient must be progressing on or since most recent therapy",
              "Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials.",
              "ECOG performance status 0-1.",
              "Participants must have adequate organ and marrow function as defined below:",
              "Leukocytes >=3,000/mcL",
              "Absolute neutrophil count >=1,500/mcL"
            ],
            "exclusion": [
              "Women who are pregnant or lactating. Pregnant women are excluded from this study because SG and EV have potential for teratogenic or abortifacient effects. Because there is an unknown but potential risk for adverse events in nursing infants secondary to treatment of the mother with EV or SG, breastfeeding should be discontinued if the mother is treated on protocol.",
              "Have had a prior anti-cancer biologic agent (including immune checkpoint inhibitors) within 4 weeks prior to Cycle 1 Day 1 (C1D1) or have had prior chemotherapy, targeted small molecule therapy, or radiation therapy within 2 weeks prior to C1D1. Subjects participating in observational studies are eligible.",
              "Presence of any toxicities attributed to prior anti-cancer therapy that are not resolved to Grade 1 or baseline that could impose serious risk for complications before administration of study drug agent",
              "Note: If subjects received major surgery, they must have recovered adequately from the toxicity and/or complications from the intervention prior to starting therapy.",
              "Have previously received topoisomerase 1 inhibitors, SG or EV",
              "Have an active second malignancy. Subjects with a history of malignancy that have been completely treated, with no evidence of active cancer for 3 years prior to start of therapy on trial (Cycle 1 Day 1 \\[C1D1\\]), or subjects with surgically-cured tumors with low risk of recurrence are allowed to enroll.",
              "Have known active central nervous system (CNS) metastases and/or carcinomatous meningitis. Subjects with previously treated brain metastases may participate provided they have stable CNS disease for at least 4 weeks prior to the first dose of study drug and all neurologic symptoms have returned to baseline, have no evidence of new or enlarging brain metastases, and are taking <=20 mg/day of prednisone or its equivalent. All subjects with carcinomatous meningitis are excluded regardless of clinical stability.",
              "Have active cardiac disease, defined as:",
              "Myocardial infarction or unstable angina pectoris within 6 months prior to C1D1",
              "History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation), high-grade atrioventricular block, or other cardiac arrhythmias requiring anti-arrhythmic medications (except for atrial fibrillation that is well controlled with antiarrhythmic medication); history of QT interval prolongation"
            ],
            "eligibility_criteria_excerpt": "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination) Inclusion Criteria: * Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible. * Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor. * Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease * Patient must be progressing on or since most recent therapy * Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials. * ECOG performance status 0-1. * Participants must have adequate organ and marrow function as defined below: * Leukocytes >=3,000/mcL * Absolute neutrophil count >=1,50"
          }
        },
        {
          "trial_id": "NCT06830031",
          "title": "Clinical Study of C402-CD19-CAR Treatment in Subjects With Relapsed or Refractory B-cell Lymphoma",
          "source_url": "https://clinicaltrials.gov/study/NCT06830031",
          "retrieval_rank": 4,
          "retrieval_score": 186.666,
          "conditions": [
            "Diffuse Large B-cell-lymphoma",
            "DLBCL, Nos Genetic Subtypes",
            "Follicular Lymphoma Grade 3B",
            "PMBL",
            "HGBL With MYC and BCL2 and/or BCL6 Rearrangements",
            "HGBL, Nos"
          ],
          "phase": "PHASE1",
          "status": "RECRUITING",
          "interventions": [
            "C402-CD19-CAR"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06830031-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Diffuse Large B-cell-lymphoma",
                "DLBCL, Nos Genetic Subtypes",
                "Follicular Lymphoma Grade 3B",
                "PMBL",
                "HGBL With MYC and BCL2 and/or BCL6 Rearrangements",
                "HGBL, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06830031-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            },
            {
              "criterion_id": "NCT06830031-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Male or female 18-75 years (inclusive);",
              "2. Patients can understand this study and capable of providing informed consent;",
              "3. Patients with willingness to be in the study and comply with the study visit procedures and other protocol requirements;",
              "4. Diagnosed with CD19-positive large B-cell lymphoma (LBCL) based on cytology or histology according to the WHO 2016 standards, including diffuse large B-cell lymphoma not otherwise specified (DLBCL-NOS), grade 3b follicular lymphoma (FL), transformed diffuse large B-cell lymphoma, primary mediastinal B-cell lymphoma (PMBL), high-grade B-cell lymphoma (HGBL) with MYC, BCL-2, and/or BCL-6 rearrangements, and high-grade B-cell lymphoma not otherwise specified (HGBL-NOS). For CD19 expression status, subjects with a clear past record of tumor histological diagnosis as CD19-positive (within 6 months prior to screening with no CD19-related treatment in the last 6 months) and tumors showing CD19-positive lymphoma levels >= 50% by IHC or CD19-positive lymphoma levels >= 70% by flow cytometry. If there is no previous CD19 tumor testing or the result is over 6 months prior to screening, a new tumor pathology sample must be provided or re-collected for CD19-positive diagnosis by the institution, with IHC showing CD19-positive lymphoma levels >= 50% or flow cytometry showing CD19-positive lymphoma levels >= 70%.",
              "5. For refractory or relapsed large B-cell lymphoma subjects, must have received at least anthracycline-based therapy and rituximab (or other CD20-targeted drugs, excluding CD20-negative cases). If previously treated with R-CHOP or other CD20-targeted therapy, the best treatment outcome prior to relapse must have been complete remission (CR). Subjects should meet the criteria for relapse, progression, or failure after second-line therapy; or relapse after autologous hematopoietic stem cell transplantation (auto-HSCT). If the subject has undergone previous auto-HSCT, the best treatment outcome prior to relapse must have been CR, and the relapse should occur more than 12 months after the previous treatment. (Refractory is defined as the best response to the most recent treatment being disease progression or stable disease after at least 2 cycles of the last-line therapy).",
              "6. According to the 2014 Lugano Treatment Response Assessment Criteria, at least one measurable tumor lesion should be present (lesions can be measured with PET results; lymph node lesions \\[long axis LDi \\> 15mm\\] or extra nodal lesions \\[long axis LDi \\> 10mm\\]);",
              "7. Expected survival time greater than 12 weeks;",
              "8. ECOG score of 0-1;",
              "9. Able to establish an intravenous route for PBMC collection, meeting the following hematologic parameters before screening: Hemoglobin >= 80 g/L, absolute neutrophil count >= 1.0 10\\^9/L, platelet count >= 75 10\\^9/L, lymphocyte count >= 0.5 10\\^9/L (if using bone marrow stimulants or blood transfusion, a washout period of 7 days is required; for granulocyte colony-stimulating factor \\[G-CSF\\] or granulocyte-macrophage colony-stimulating factor \\[GM-CSF\\], a washout period of 4 weeks or 5 half-lives is required);",
              "10. Liver and kidney function, as well as heart and lung function, should meet the following requirements:"
            ],
            "exclusion": [
              "1. History of receiving allogeneic hematopoietic stem cell transplantation, adoptive cell therapy (such as CAR-T therapy), or other gene-modified cell therapies;",
              "2. Any active central nervous system (CNS) involvement (including symptomatic and asymptomatic), or a history of CNS disease (such as epilepsy, cerebral ischemia/hemorrhage, dementia, cerebellar disorders, or any autoimmune diseases involving the CNS);",
              "3. Positive for hepatitis B surface antigen (HBsAg) or hepatitis B core antibody (HBcAb) with peripheral blood HBV DNA positivity, or subjects with HBV titers above the upper limit of the normal range for the study center; positive for hepatitis C virus (HCV) antibody and peripheral blood HCV RNA positivity; positive for cytomegalovirus (CMV) DNA; positive for human immunodeficiency virus (HIV) antibody; positive for syphilis test;",
              "4. Any unstable systemic disease, including but not limited to unstable angina, cerebrovascular accident or transient ischemic attack (within 6 months prior to screening), myocardial infarction (within 6 months prior to screening), congestive heart failure (New York Heart Association \\[NYHA\\] classification >= III), active bleeding, severe arrhythmias requiring drug treatment, liver, kidney, or metabolic disorders;",
              "5. Presence of malignant tumors other than large B-cell lymphoma, except for cured non-melanoma skin cancer, carcinoma in situ of the cervix, localized prostate cancer, superficial bladder cancer, ductal carcinoma in situ, and other cancers with a disease-free survival of more than 5 years;",
              "6. Presence of gastric lymphoma, bulky disease, a history of CD19+ leukemia, or active autoimmune diseases (e.g., systemic lupus erythematosus, Sjgren's syndrome, rheumatoid arthritis, psoriasis, multiple sclerosis, inflammatory bowel disease, Hashimoto's thyroiditis, etc.);",
              "7. Presence of uncontrolled active infections requiring treatment (e.g., sepsis, bacteremia, fungemia, viremia) (mild urinary tract infections or upper respiratory tract infections are exceptions), with the exception of prophylactic anti-infection treatment (for bacterial, fungal, viral infections, etc.);",
              "8. Subjects who have received systemic steroid treatment within 2 weeks before PBMC collection and are determined by the investigator to require long-term systemic steroid treatment during the treatment period (except for inhaled, local application, or physiological replacement doses \\[hydrocortisone <=7 mgd-1 or equivalent prednisone <=5 mgd-1 or dexamethasone <=0.5 mgd-1\\]);",
              "9. Subjects who have received anti-tumor treatment within 8 weeks or 5 half-lives (specific medications need to be assessed in detail) before PBMC collection, including chemotherapy, CD20-targeted therapy, etc.; local radiotherapy within 12 weeks;",
              "10. Subjects who have used granulocyte colony-stimulating factor (G-CSF) or granulocyte-macrophage colony-stimulating factor (GM-CSF) within 4 weeks before PBMC collection or within at least 5 half-lives (whichever is shorter);"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: Must meet all the following inclusion criteria: 1. Male or female 18-75 years (inclusive); 2. Patients can understand this study and capable of providing informed consent; 3. Patients with willingness to be in the study and comply with the study visit procedures and other protocol requirements; 4. Diagnosed with CD19-positive large B-cell lymphoma (LBCL) based on cytology or histology according to the WHO 2016 standards, including diffuse large B-cell lymphoma not otherwise specified (DLBCL-NOS), grade 3b follicular lymphoma (FL), transformed diffuse large B-cell lymphoma, primary mediastinal B-cell lymphoma (PMBL), high-grade B-cell lymphoma (HGBL) with MYC, BCL-2, and/or BCL-6 rearrangements, and high-grade B-cell lymphoma not otherwise specified (HGBL-NOS). For CD19 expression status, subjects with a clear past record of tumor histological diagnosis as CD19-positive (within 6 months prior to screening with no CD19-related treatment in the last 6 months) and tumors showing CD19-positive lymphoma levels >= 50% by IHC or CD19-positive lymphoma levels >= 70% by flow cytometry. If there is no previous CD19 tumor testing or the result is over 6 months prior to screening, a new tumor pathology sample must be provided or re-collected for CD19-positive diagnosis by the institution, with IHC showing CD19-positive lymphoma levels >= 50% or flow cytometry showing CD19-positive lymphoma levels >= 70%. 5. For refractory or relapsed large B-cell lymphoma subjects, must have received at least anthracycline-based therapy and rituximab (or other CD20-targeted drugs, excluding CD20-negative cases). If previously treated with R-CHOP or other CD20-targeted therapy, the best treatment outcome prior to relapse must have been complete remission (CR). Subjects should meet"
          }
        },
        {
          "trial_id": "NCT07091617",
          "title": "Testing an Enhanced Digital Delivery Model for Inherited Cancer Genetic Testing in Young Adults With Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT07091617",
          "retrieval_rank": 5,
          "retrieval_score": 170.734,
          "conditions": [
            "Miscellaneous Neoplasm, Nos",
            "Non-Neoplastic Condition, Nos"
          ],
          "phase": "NA",
          "status": "RECRUITING",
          "interventions": [
            "Telemedicine",
            "Genetic Testing",
            "Telemedicine",
            "Internet-Based Intervention",
            "Educational Intervention",
            "Patient Navigation",
            "Interview",
            "Survey Administration"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07091617-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Miscellaneous Neoplasm, Nos",
                "Non-Neoplastic Condition, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment",
              "PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not",
              "PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish",
              "PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members",
              "PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician",
              "PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review",
              "NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial services and/or for insurance companies) who participate in oncology care among AYA in community for this study",
              "NON-PATIENT PARTICIPANT: Age >= 18 years",
              "NON-PATIENT PARTICIPANT: Non-patient participants must be able to speak and read English or Spanish in order to participate in the key informant interviews"
            ],
            "exclusion": [],
            "eligibility_criteria_excerpt": "* PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment * PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not * PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish * PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members * PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician * PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review * NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial servic"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00017",
      "patient_information_string": "Oncology referral note: SYN-GEN-00017 is a 45-year-old male with thyroid eye disease. Stage is recorded as IV. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in FL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00017",
        "age": 45,
        "sex": "male",
        "diagnosis": "thyroid eye disease",
        "stage": "IV",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "FL"
        },
        "scenario": "clear_candidate",
        "target_trial_id": "NCT06625411"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT06625411",
          "title": "An Efficacy, Safety, and Tolerability Study of VRDN-003 in Participants With Active Thyroid Eye Disease (TED)",
          "source_url": "https://clinicaltrials.gov/study/NCT06625411",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Thyroid Eye Disease"
          ],
          "phase": "PHASE3",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "VRDN-003",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06625411-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06625411-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Must have moderate to severe active TED with documented evidence of ocular symptoms or signs that began within 15 months prior to screening",
              "Must have a Clinical Activity Score (CAS) of >= 3 on the 7-item scale for the study eye",
              "Must agree to use highly effective contraception as specified in the protocol",
              "Female TED participants must have a negative serum pregnancy test at screening"
            ],
            "exclusion": [
              "Must not have received prior treatment with another anti-IGF-1R therapy",
              "Must not have received systemic corticosteroids or steroid eye drops for any condition, including TED, or selenium within 2 weeks prior to first dose",
              "Must not have received other immunosuppressive drugs for any condition, including TED, or any other therapy for TED within 12 weeks prior to first dose.",
              "Must not have received an investigational agent for any condition, including TED, within 8 weeks or longer duration (depending on the type of investigational agent) prior to first dose",
              "Must not have received radioactive iodine (RAI) treatment within 8 weeks prior to first dose",
              "Must not have had previous orbital irradiation or decompression surgery for TED to the study eye's orbit",
              "Must not have a pre-existing ophthalmic condition in the study eye which in the study doctor's opinion, would interfere with interpretation of study results",
              "Must not have abnormal hearing test before first dose. Must also not have a history of ear conditions considered significant by study doctor",
              "Must not have a history of inflammatory bowel disease",
              "Female TED participants who must not be pregnant or breastfeeding"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: * Must have moderate to severe active TED with documented evidence of ocular symptoms or signs that began within 15 months prior to screening * Must have a Clinical Activity Score (CAS) of >= 3 on the 7-item scale for the study eye * Must agree to use highly effective contraception as specified in the protocol * Female TED participants must have a negative serum pregnancy test at screening Key Exclusion Criteria: * Must not have received prior treatment with another anti-IGF-1R therapy * Must not have received systemic corticosteroids or steroid eye drops for any condition, including TED, or selenium within 2 weeks prior to first dose * Must not have received other immunosuppressive drugs for any condition, including TED, or any other therapy for TED within 12 weeks prior to first dose. * Must not have received an investigational agent for any condition, including TED, within 8 weeks or longer duration (depending on the type of investigational agent) prior to first dose * Must not have received radioactive iodine (RAI) treatment within 8 weeks prior to first dose * Must not have had previous orbital irradiation or decompression surgery for TED to the study eye's orbit * Must not have a pre-existing ophthalmic condition in the study eye which in the study doctor's opinion, would interfere with interpretation of study results * Must not have abnormal hearing test before first dose. Must also not have a history of ear conditions considered significant by study doctor * Must not have a history of inflammatory bowel disease * Female TED participants who must not be pregnant or breastfeeding NOTE: There are additional eligibility criteria for participants who do not have a meaningful response at Week 24 (irrespective of initial treatment arm) who may r"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 279.734,
          "conditions": [
            "Locally Advanced Bladder Urothelial Carcinoma",
            "Locally Advanced Renal Pelvis Urothelial Carcinoma",
            "Locally Advanced Ureter Urothelial Carcinoma",
            "Locally Advanced Urethral Urothelial Carcinoma",
            "Metastatic Bladder Urothelial Carcinoma",
            "Metastatic Renal Pelvis Urothelial Carcinoma",
            "Metastatic Ureter Urothelial Carcinoma",
            "Metastatic Urethral Urothelial Carcinoma",
            "Recurrent Bladder Urothelial Carcinoma",
            "Recurrent Renal Pelvis Urothelial Carcinoma",
            "Recurrent Ureter Urothelial Carcinoma",
            "Recurrent Urethral Urothelial Carcinoma",
            "Stage III Bladder Cancer AJCC v8",
            "Stage III Renal Pelvis Cancer AJCC v8",
            "Stage III Ureter Cancer AJCC v8",
            "Stage III Urethral Cancer AJCC v8",
            "Stage IV Bladder Cancer AJCC v8",
            "Stage IV Renal Pelvis Cancer AJCC v8",
            "Stage IV Ureter Cancer AJCC v8",
            "Stage IV Urethral Cancer AJCC v8",
            "Unresectable Bladder Urothelial Carcinoma",
            "Unresectable Renal Pelvis Urothelial Carcinoma",
            "Unresectable Ureter Urothelial Carcinoma",
            "Unresectable Urethral Urothelial Carcinoma"
          ],
          "phase": "PHASE2",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Atezolizumab",
            "Biopsy Procedure",
            "Biospecimen Collection",
            "Computed Tomography with Contrast",
            "Eribulin Mesylate"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 2,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03237780-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Locally Advanced Bladder Urothelial Carcinoma",
                "Locally Advanced Renal Pelvis Urothelial Carcinoma",
                "Locally Advanced Ureter Urothelial Carcinoma",
                "Locally Advanced Urethral Urothelial Carcinoma",
                "Metastatic Bladder Urothelial Carcinoma",
                "Metastatic Renal Pelvis Urothelial Carcinoma",
                "Metastatic Ureter Urothelial Carcinoma",
                "Metastatic Urethral Urothelial Carcinoma",
                "Recurrent Bladder Urothelial Carcinoma",
                "Recurrent Renal Pelvis Urothelial Carcinoma",
                "Recurrent Ureter Urothelial Carcinoma",
                "Recurrent Urethral Urothelial Carcinoma",
                "Stage III Bladder Cancer AJCC v8",
                "Stage III Renal Pelvis Cancer AJCC v8",
                "Stage III Ureter Cancer AJCC v8",
                "Stage III Urethral Cancer AJCC v8",
                "Stage IV Bladder Cancer AJCC v8",
                "Stage IV Renal Pelvis Cancer AJCC v8",
                "Stage IV Ureter Cancer AJCC v8",
                "Stage IV Urethral Cancer AJCC v8",
                "Unresectable Bladder Urothelial Carcinoma",
                "Unresectable Renal Pelvis Urothelial Carcinoma",
                "Unresectable Ureter Urothelial Carcinoma",
                "Unresectable Urethral Urothelial Carcinoma"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 2,
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study",
              "Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra",
              "Presence of measurable disease meeting the following criteria:",
              "At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm",
              "Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion",
              "Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence",
              "PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to allow for stratification; COMMERCIAL ASSESSMENT OF PD-L1 STATUS OBTAINED LOCALLY AT THE SITE WILL NOT SATISFY ELIGIBILITY CRITERIA",
              "New, progressive or recurrent disease occurring",
              "During or within 12 months of treatment with a platinum containing regimen (cisplatin or carboplatin or novel platinum) in either in the metastatic or perioperative setting",
              "In first-line patients defined as cisplatin-ineligible based on renal impairment (creatinine clearance calculated by Cockcroft-Gault method \\< 60 ml/min), at least grade 2 hearing loss and/or Eastern Cooperative Oncology Group (ECOG) status of 2; these patients will be chemotherapy naive or have received platinum based therapy in the adjuvant or neoadjuvant setting more than 12 months prior to study entry"
            ],
            "exclusion": [
              "Patients with prior allogeneic bone marrow transplantation or prior solid organ transplantation",
              "Patients who have had chemotherapy within 3 weeks or radiotherapy or targeted therapy 2 weeks (6 weeks for nitrosoureas or mitomycin C) prior to entering the study or those who have not recovered from adverse events (other than alopecia) due to agents administered more than 4 weeks earlier; however, the following therapies are allowed:",
              "Hormone-replacement therapy or oral contraceptives",
              "Herbal therapy \\> 1 week prior to cycle 1, day 1 (herbal therapy intended as anticancer therapy must be discontinued at least 1 week prior to cycle 1, day 1)",
              "Palliative radiotherapy for bone metastases \\> 2 weeks prior to cycle 1, day 1",
              "Prior treatment with anti-PD-1, or anti-PD-L1 therapeutic antibody or pathway-targeting agents or eribulin",
              "Patients who have received prior treatment with anti-CTLA-4 may be enrolled, provided the following requirements are met:",
              "Minimum of 12 weeks from the first dose of anti-CTLA-4 and \\> 6 weeks from the last dose",
              "No history of severe immune-related adverse effects from anti-CTLA-4 (National Cancer Institute \\[NCI\\] Common Terminology Criteria for Adverse Events \\[CTCAE\\] version 5.0)",
              "Treatment with any other investigational agent within 4 weeks prior to cycle 1, day 1"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study * Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra * Presence of measurable disease meeting the following criteria: * At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm * Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion * Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence * PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 3,
          "retrieval_score": 214.584,
          "conditions": [
            "Urothelial Cancer",
            "Metastatic Urothelial Carcinoma",
            "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
            "Bladder Cancer"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Sacituzumab Govitecan (SG)",
            "Enfortumab vedotin-ejfv (EV)",
            "Pembrolizumab"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04724018-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Urothelial Cancer",
                "Metastatic Urothelial Carcinoma",
                "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
                "Bladder Cancer"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination)",
              "Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible.",
              "Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor.",
              "Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease",
              "Patient must be progressing on or since most recent therapy",
              "Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials.",
              "ECOG performance status 0-1.",
              "Participants must have adequate organ and marrow function as defined below:",
              "Leukocytes >=3,000/mcL",
              "Absolute neutrophil count >=1,500/mcL"
            ],
            "exclusion": [
              "Women who are pregnant or lactating. Pregnant women are excluded from this study because SG and EV have potential for teratogenic or abortifacient effects. Because there is an unknown but potential risk for adverse events in nursing infants secondary to treatment of the mother with EV or SG, breastfeeding should be discontinued if the mother is treated on protocol.",
              "Have had a prior anti-cancer biologic agent (including immune checkpoint inhibitors) within 4 weeks prior to Cycle 1 Day 1 (C1D1) or have had prior chemotherapy, targeted small molecule therapy, or radiation therapy within 2 weeks prior to C1D1. Subjects participating in observational studies are eligible.",
              "Presence of any toxicities attributed to prior anti-cancer therapy that are not resolved to Grade 1 or baseline that could impose serious risk for complications before administration of study drug agent",
              "Note: If subjects received major surgery, they must have recovered adequately from the toxicity and/or complications from the intervention prior to starting therapy.",
              "Have previously received topoisomerase 1 inhibitors, SG or EV",
              "Have an active second malignancy. Subjects with a history of malignancy that have been completely treated, with no evidence of active cancer for 3 years prior to start of therapy on trial (Cycle 1 Day 1 \\[C1D1\\]), or subjects with surgically-cured tumors with low risk of recurrence are allowed to enroll.",
              "Have known active central nervous system (CNS) metastases and/or carcinomatous meningitis. Subjects with previously treated brain metastases may participate provided they have stable CNS disease for at least 4 weeks prior to the first dose of study drug and all neurologic symptoms have returned to baseline, have no evidence of new or enlarging brain metastases, and are taking <=20 mg/day of prednisone or its equivalent. All subjects with carcinomatous meningitis are excluded regardless of clinical stability.",
              "Have active cardiac disease, defined as:",
              "Myocardial infarction or unstable angina pectoris within 6 months prior to C1D1",
              "History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation), high-grade atrioventricular block, or other cardiac arrhythmias requiring anti-arrhythmic medications (except for atrial fibrillation that is well controlled with antiarrhythmic medication); history of QT interval prolongation"
            ],
            "eligibility_criteria_excerpt": "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination) Inclusion Criteria: * Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible. * Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor. * Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease * Patient must be progressing on or since most recent therapy * Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials. * ECOG performance status 0-1. * Participants must have adequate organ and marrow function as defined below: * Leukocytes >=3,000/mcL * Absolute neutrophil count >=1,50"
          }
        },
        {
          "trial_id": "NCT07622368",
          "title": "A Study of IBI3031 in Participants With Thyroid Eye Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT07622368",
          "retrieval_rank": 4,
          "retrieval_score": 212.119,
          "conditions": [
            "Thyroid Eye Disease"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "IBI3031",
            "placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07622368-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07622368-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Written informed consent.",
              "2. Aged between 18 and 75 years at screening.",
              "3. Weight between 45 kg and 100 kg.",
              "4. Moderate-to-severe active TED:",
              "CAS >= 3 in the study eye at screening and baseline;",
              "Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia;",
              "<= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening;",
              "5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2)",
              "6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening.",
              "7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening."
            ],
            "exclusion": [
              "Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible):",
              "1. The CAS of the study eye at baseline is reduced by >= 2 points compared with that at screening, or the proptosis of the study eye at baseline is reduced by >= 2 mm compared with that at screening;",
              "2. Participants previously diagnosed with dysthyroid optic neuropathy (DON), or with DON as determined by the investigator at screening;",
              "3. Patients with corneal ulcers that are not relieved after treatment at the investigator's discretion;",
              "4. Presence of other non-TED ophthalmic diseases that may affect the interpretation of study results or the safety of participants as determined by the investigator (e.g., proptosis not primarily caused by TED);",
              "5. At screening, clinical or laboratory evidence of significant hypothyroidism (presence of clinical symptoms of hypothyroidism, or FT3 or FT4 (Free Thyroxine)\\<0.5lower limit of normal \\[LLN\\], or TSH\\>1.5upper limit of normal \\[ULN\\]); or severe hyperthyroidism during the screening period (FT3 and FT4(Free Thyroxine)\\>2ULN, or presence of thyroid storm).",
              "6. Other medical history and abnormal test results during the screening period that are judged by the investigator to be clinically significant, may cause the participant to fail to comply with the study protocol or complete the trial, or endanger safety, including but not limited to:",
              "History of hepatic insufficiency (Child-Pugh Class B or C) or liver cirrhosis; aspartate aminotransferase (AST) or alanine aminotransferase (ALT) \\> 2 ULN at screening;",
              "Glomerular filtration rate (GFR) \\< 60 ml/min/1.73 m2;",
              "Poorly controlled diabetes mellitus or hypertension;"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: 1. Written informed consent. 2. Aged between 18 and 75 years at screening. 3. Weight between 45 kg and 100 kg. 4. Moderate-to-severe active TED: * CAS >= 3 in the study eye at screening and baseline; * Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia; * <= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening; 5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2) 6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening. 7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening. 8. No prior treatment with antithyroid medications and/or thyroid hormone replacement therapy, or having taken antithyroid medications and/or thyroid hormone replacement therapy on a stable dose for at least 6 weeks prior to the first dose, or having not been treated with antithyroid medications and/or thyroid hormone replacement therapy due to intolerable side effects for at least 6 weeks prior to the first dose. 9. Infertile female participants or fertile female participants with negative blood pregnancy test results during the screening period and agree to take contraceptive measures from screening to 120 days after the last dose; male participants should agree to use contraceptive measures from screening to 120 days after the last dose. Key Exclusion Criteria: Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible): 1. The CAS of the study eye at baseline is reduced by >= 2 points com"
          }
        },
        {
          "trial_id": "NCT07091617",
          "title": "Testing an Enhanced Digital Delivery Model for Inherited Cancer Genetic Testing in Young Adults With Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT07091617",
          "retrieval_rank": 5,
          "retrieval_score": 186.359,
          "conditions": [
            "Miscellaneous Neoplasm, Nos",
            "Non-Neoplastic Condition, Nos"
          ],
          "phase": "NA",
          "status": "RECRUITING",
          "interventions": [
            "Telemedicine",
            "Genetic Testing",
            "Telemedicine",
            "Internet-Based Intervention",
            "Educational Intervention",
            "Patient Navigation",
            "Interview",
            "Survey Administration"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07091617-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Miscellaneous Neoplasm, Nos",
                "Non-Neoplastic Condition, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment",
              "PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not",
              "PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish",
              "PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members",
              "PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician",
              "PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review",
              "NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial services and/or for insurance companies) who participate in oncology care among AYA in community for this study",
              "NON-PATIENT PARTICIPANT: Age >= 18 years",
              "NON-PATIENT PARTICIPANT: Non-patient participants must be able to speak and read English or Spanish in order to participate in the key informant interviews"
            ],
            "exclusion": [],
            "eligibility_criteria_excerpt": "* PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment * PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not * PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish * PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members * PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician * PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review * NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial servic"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00018",
      "patient_information_string": "Tumor board intake: SYN-GEN-00018 is a 40-year-old male with thyroid eye disease (ted). Stage is recorded as IV. ECOG performance status is 1. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in PA. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00018",
        "age": 40,
        "sex": "male",
        "diagnosis": "thyroid eye disease (ted)",
        "stage": "IV",
        "ecog": 1,
        "location": {
          "country": "US",
          "state": "PA"
        },
        "scenario": "missing_biomarker",
        "target_trial_id": "NCT07404111"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07404111",
          "title": "A Study of VV-14305 for the Treatment of Thyroid Eye Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT07404111",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Thyroid Eye Disease (TED)"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "VV-14305",
            "Sham (No Treatment)"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 80,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07404111-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease (TED)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07404111-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 80
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Must be 18 to 80 years of age (inclusive) at Screening.",
              "2. Body Mass Index (BMI) of 19 to 34 kg/m2 (inclusive).",
              "3. Must be euthyroid (defined as normal thyroid-stimulating hormone) or have mild hyper- or hypothyroidism (being managed to bring them to a euthyroid state).",
              "4. Best Corrected Visual Acuity (BCVA) score of 20/60 or better at Screening with no history of deterioration noted in the 3 months prior to Screening.",
              "5. Must be willing and able to cease product use prior to VV-14305 (or sham) peribulbar injection if using non-steroidal anti-inflammatory drug (NSAIDs), medications or any herbal supplements, vitamins, or multivitamins with antiplatelet/anticoagulant properties.",
              "6. The study eye and the fellow eye must fall within the pre-defined degree of proptosis and clinical activity score (CAS) as measured at Screening.",
              "7. Participants must be diagnosed with TED prior to Screening and be diagnosed with Graves' disease and progressive moderate to severe TED at Screening."
            ],
            "exclusion": [
              "1. History of serious ocular condition(s) other than TED, including but not limited to uveitis, dry age-related macular degeneration (AMD), and wet AMD; Other orbital or ophthalmic diseases, including inflammatory conditions, optic neuropathy, tumors, glaucoma with visual field defect or visual field loss, that in the opinion of the Investigator and/or Medical Monitor is clinically significant.",
              "2. Any medical, cognitive, or psychiatric condition that, in the opinion of the Investigator, could contraindicate the use of the investigational drug, make consistent study assessment and follow-up over the 12-month Post-Treatment Follow-up Period unlikely, or would make the participant an unsafe study candidate.",
              "3. Diagnosed with diabetes (HbA1c >=6.5%).",
              "4. History of malignancy requiring chemotherapy and/or radiation in the 12 months prior to Screening, except for successfully treated nonmelanoma skin cancers (e.g., basal cell, squamous cell carcinomas), cervical intraepithelial neoplasia, and localized prostate cancer.",
              "5. Known allergy or condition that would contraindicate the use of required study medications.",
              "6. Any Screening assessment or laboratory value that, in the opinion of the Investigator and/or Medical Monitor, is clinically significant and renders the subject not suitable for study participation.",
              "7. Any vaccination or planned vaccination 30 days prior to dosing, 4 weeks post dosing or during period of immunosuppression.",
              "8. Participant requires or, in the opinion of the Investigator, is likely to require immediate surgical ophthalmological/orbital intervention or irradiation of either eye; Has had any prior surgery for TED including orbital decompression, strabismus surgery and any eyelid surgery on either eye.",
              "9. Prior participation in other gene therapy, investigational drug, biologic or device clinical trials within 30 days prior to Screening."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1. Must be 18 to 80 years of age (inclusive) at Screening. 2. Body Mass Index (BMI) of 19 to 34 kg/m2 (inclusive). 3. Must be euthyroid (defined as normal thyroid-stimulating hormone) or have mild hyper- or hypothyroidism (being managed to bring them to a euthyroid state). 4. Best Corrected Visual Acuity (BCVA) score of 20/60 or better at Screening with no history of deterioration noted in the 3 months prior to Screening. 5. Must be willing and able to cease product use prior to VV-14305 (or sham) peribulbar injection if using non-steroidal anti-inflammatory drug (NSAIDs), medications or any herbal supplements, vitamins, or multivitamins with antiplatelet/anticoagulant properties. 6. The study eye and the fellow eye must fall within the pre-defined degree of proptosis and clinical activity score (CAS) as measured at Screening. 7. Participants must be diagnosed with TED prior to Screening and be diagnosed with Graves' disease and progressive moderate to severe TED at Screening. Exclusion Criteria: 1. History of serious ocular condition(s) other than TED, including but not limited to uveitis, dry age-related macular degeneration (AMD), and wet AMD; Other orbital or ophthalmic diseases, including inflammatory conditions, optic neuropathy, tumors, glaucoma with visual field defect or visual field loss, that in the opinion of the Investigator and/or Medical Monitor is clinically significant. 2. Any medical, cognitive, or psychiatric condition that, in the opinion of the Investigator, could contraindicate the use of the investigational drug, make consistent study assessment and follow-up over the 12-month Post-Treatment Follow-up Period unlikely, or would make the participant an unsafe study candidate. 3. Diagnosed with diabetes (HbA1c >=6.5%). 4. History "
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 298.573,
          "conditions": [
            "Locally Advanced Bladder Urothelial Carcinoma",
            "Locally Advanced Renal Pelvis Urothelial Carcinoma",
            "Locally Advanced Ureter Urothelial Carcinoma",
            "Locally Advanced Urethral Urothelial Carcinoma",
            "Metastatic Bladder Urothelial Carcinoma",
            "Metastatic Renal Pelvis Urothelial Carcinoma",
            "Metastatic Ureter Urothelial Carcinoma",
            "Metastatic Urethral Urothelial Carcinoma",
            "Recurrent Bladder Urothelial Carcinoma",
            "Recurrent Renal Pelvis Urothelial Carcinoma",
            "Recurrent Ureter Urothelial Carcinoma",
            "Recurrent Urethral Urothelial Carcinoma",
            "Stage III Bladder Cancer AJCC v8",
            "Stage III Renal Pelvis Cancer AJCC v8",
            "Stage III Ureter Cancer AJCC v8",
            "Stage III Urethral Cancer AJCC v8",
            "Stage IV Bladder Cancer AJCC v8",
            "Stage IV Renal Pelvis Cancer AJCC v8",
            "Stage IV Ureter Cancer AJCC v8",
            "Stage IV Urethral Cancer AJCC v8",
            "Unresectable Bladder Urothelial Carcinoma",
            "Unresectable Renal Pelvis Urothelial Carcinoma",
            "Unresectable Ureter Urothelial Carcinoma",
            "Unresectable Urethral Urothelial Carcinoma"
          ],
          "phase": "PHASE2",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Atezolizumab",
            "Biopsy Procedure",
            "Biospecimen Collection",
            "Computed Tomography with Contrast",
            "Eribulin Mesylate"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 2,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03237780-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Locally Advanced Bladder Urothelial Carcinoma",
                "Locally Advanced Renal Pelvis Urothelial Carcinoma",
                "Locally Advanced Ureter Urothelial Carcinoma",
                "Locally Advanced Urethral Urothelial Carcinoma",
                "Metastatic Bladder Urothelial Carcinoma",
                "Metastatic Renal Pelvis Urothelial Carcinoma",
                "Metastatic Ureter Urothelial Carcinoma",
                "Metastatic Urethral Urothelial Carcinoma",
                "Recurrent Bladder Urothelial Carcinoma",
                "Recurrent Renal Pelvis Urothelial Carcinoma",
                "Recurrent Ureter Urothelial Carcinoma",
                "Recurrent Urethral Urothelial Carcinoma",
                "Stage III Bladder Cancer AJCC v8",
                "Stage III Renal Pelvis Cancer AJCC v8",
                "Stage III Ureter Cancer AJCC v8",
                "Stage III Urethral Cancer AJCC v8",
                "Stage IV Bladder Cancer AJCC v8",
                "Stage IV Renal Pelvis Cancer AJCC v8",
                "Stage IV Ureter Cancer AJCC v8",
                "Stage IV Urethral Cancer AJCC v8",
                "Unresectable Bladder Urothelial Carcinoma",
                "Unresectable Renal Pelvis Urothelial Carcinoma",
                "Unresectable Ureter Urothelial Carcinoma",
                "Unresectable Urethral Urothelial Carcinoma"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 2,
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study",
              "Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra",
              "Presence of measurable disease meeting the following criteria:",
              "At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm",
              "Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion",
              "Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence",
              "PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to allow for stratification; COMMERCIAL ASSESSMENT OF PD-L1 STATUS OBTAINED LOCALLY AT THE SITE WILL NOT SATISFY ELIGIBILITY CRITERIA",
              "New, progressive or recurrent disease occurring",
              "During or within 12 months of treatment with a platinum containing regimen (cisplatin or carboplatin or novel platinum) in either in the metastatic or perioperative setting",
              "In first-line patients defined as cisplatin-ineligible based on renal impairment (creatinine clearance calculated by Cockcroft-Gault method \\< 60 ml/min), at least grade 2 hearing loss and/or Eastern Cooperative Oncology Group (ECOG) status of 2; these patients will be chemotherapy naive or have received platinum based therapy in the adjuvant or neoadjuvant setting more than 12 months prior to study entry"
            ],
            "exclusion": [
              "Patients with prior allogeneic bone marrow transplantation or prior solid organ transplantation",
              "Patients who have had chemotherapy within 3 weeks or radiotherapy or targeted therapy 2 weeks (6 weeks for nitrosoureas or mitomycin C) prior to entering the study or those who have not recovered from adverse events (other than alopecia) due to agents administered more than 4 weeks earlier; however, the following therapies are allowed:",
              "Hormone-replacement therapy or oral contraceptives",
              "Herbal therapy \\> 1 week prior to cycle 1, day 1 (herbal therapy intended as anticancer therapy must be discontinued at least 1 week prior to cycle 1, day 1)",
              "Palliative radiotherapy for bone metastases \\> 2 weeks prior to cycle 1, day 1",
              "Prior treatment with anti-PD-1, or anti-PD-L1 therapeutic antibody or pathway-targeting agents or eribulin",
              "Patients who have received prior treatment with anti-CTLA-4 may be enrolled, provided the following requirements are met:",
              "Minimum of 12 weeks from the first dose of anti-CTLA-4 and \\> 6 weeks from the last dose",
              "No history of severe immune-related adverse effects from anti-CTLA-4 (National Cancer Institute \\[NCI\\] Common Terminology Criteria for Adverse Events \\[CTCAE\\] version 5.0)",
              "Treatment with any other investigational agent within 4 weeks prior to cycle 1, day 1"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study * Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra * Presence of measurable disease meeting the following criteria: * At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm * Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion * Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence * PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to"
          }
        },
        {
          "trial_id": "NCT07622368",
          "title": "A Study of IBI3031 in Participants With Thyroid Eye Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT07622368",
          "retrieval_rank": 3,
          "retrieval_score": 253.119,
          "conditions": [
            "Thyroid Eye Disease"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "IBI3031",
            "placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07622368-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07622368-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Written informed consent.",
              "2. Aged between 18 and 75 years at screening.",
              "3. Weight between 45 kg and 100 kg.",
              "4. Moderate-to-severe active TED:",
              "CAS >= 3 in the study eye at screening and baseline;",
              "Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia;",
              "<= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening;",
              "5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2)",
              "6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening.",
              "7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening."
            ],
            "exclusion": [
              "Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible):",
              "1. The CAS of the study eye at baseline is reduced by >= 2 points compared with that at screening, or the proptosis of the study eye at baseline is reduced by >= 2 mm compared with that at screening;",
              "2. Participants previously diagnosed with dysthyroid optic neuropathy (DON), or with DON as determined by the investigator at screening;",
              "3. Patients with corneal ulcers that are not relieved after treatment at the investigator's discretion;",
              "4. Presence of other non-TED ophthalmic diseases that may affect the interpretation of study results or the safety of participants as determined by the investigator (e.g., proptosis not primarily caused by TED);",
              "5. At screening, clinical or laboratory evidence of significant hypothyroidism (presence of clinical symptoms of hypothyroidism, or FT3 or FT4 (Free Thyroxine)\\<0.5lower limit of normal \\[LLN\\], or TSH\\>1.5upper limit of normal \\[ULN\\]); or severe hyperthyroidism during the screening period (FT3 and FT4(Free Thyroxine)\\>2ULN, or presence of thyroid storm).",
              "6. Other medical history and abnormal test results during the screening period that are judged by the investigator to be clinically significant, may cause the participant to fail to comply with the study protocol or complete the trial, or endanger safety, including but not limited to:",
              "History of hepatic insufficiency (Child-Pugh Class B or C) or liver cirrhosis; aspartate aminotransferase (AST) or alanine aminotransferase (ALT) \\> 2 ULN at screening;",
              "Glomerular filtration rate (GFR) \\< 60 ml/min/1.73 m2;",
              "Poorly controlled diabetes mellitus or hypertension;"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: 1. Written informed consent. 2. Aged between 18 and 75 years at screening. 3. Weight between 45 kg and 100 kg. 4. Moderate-to-severe active TED: * CAS >= 3 in the study eye at screening and baseline; * Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia; * <= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening; 5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2) 6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening. 7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening. 8. No prior treatment with antithyroid medications and/or thyroid hormone replacement therapy, or having taken antithyroid medications and/or thyroid hormone replacement therapy on a stable dose for at least 6 weeks prior to the first dose, or having not been treated with antithyroid medications and/or thyroid hormone replacement therapy due to intolerable side effects for at least 6 weeks prior to the first dose. 9. Infertile female participants or fertile female participants with negative blood pregnancy test results during the screening period and agree to take contraceptive measures from screening to 120 days after the last dose; male participants should agree to use contraceptive measures from screening to 120 days after the last dose. Key Exclusion Criteria: Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible): 1. The CAS of the study eye at baseline is reduced by >= 2 points com"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 4,
          "retrieval_score": 237.417,
          "conditions": [
            "Urothelial Cancer",
            "Metastatic Urothelial Carcinoma",
            "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
            "Bladder Cancer"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Sacituzumab Govitecan (SG)",
            "Enfortumab vedotin-ejfv (EV)",
            "Pembrolizumab"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04724018-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Urothelial Cancer",
                "Metastatic Urothelial Carcinoma",
                "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
                "Bladder Cancer"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination)",
              "Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible.",
              "Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor.",
              "Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease",
              "Patient must be progressing on or since most recent therapy",
              "Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials.",
              "ECOG performance status 0-1.",
              "Participants must have adequate organ and marrow function as defined below:",
              "Leukocytes >=3,000/mcL",
              "Absolute neutrophil count >=1,500/mcL"
            ],
            "exclusion": [
              "Women who are pregnant or lactating. Pregnant women are excluded from this study because SG and EV have potential for teratogenic or abortifacient effects. Because there is an unknown but potential risk for adverse events in nursing infants secondary to treatment of the mother with EV or SG, breastfeeding should be discontinued if the mother is treated on protocol.",
              "Have had a prior anti-cancer biologic agent (including immune checkpoint inhibitors) within 4 weeks prior to Cycle 1 Day 1 (C1D1) or have had prior chemotherapy, targeted small molecule therapy, or radiation therapy within 2 weeks prior to C1D1. Subjects participating in observational studies are eligible.",
              "Presence of any toxicities attributed to prior anti-cancer therapy that are not resolved to Grade 1 or baseline that could impose serious risk for complications before administration of study drug agent",
              "Note: If subjects received major surgery, they must have recovered adequately from the toxicity and/or complications from the intervention prior to starting therapy.",
              "Have previously received topoisomerase 1 inhibitors, SG or EV",
              "Have an active second malignancy. Subjects with a history of malignancy that have been completely treated, with no evidence of active cancer for 3 years prior to start of therapy on trial (Cycle 1 Day 1 \\[C1D1\\]), or subjects with surgically-cured tumors with low risk of recurrence are allowed to enroll.",
              "Have known active central nervous system (CNS) metastases and/or carcinomatous meningitis. Subjects with previously treated brain metastases may participate provided they have stable CNS disease for at least 4 weeks prior to the first dose of study drug and all neurologic symptoms have returned to baseline, have no evidence of new or enlarging brain metastases, and are taking <=20 mg/day of prednisone or its equivalent. All subjects with carcinomatous meningitis are excluded regardless of clinical stability.",
              "Have active cardiac disease, defined as:",
              "Myocardial infarction or unstable angina pectoris within 6 months prior to C1D1",
              "History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation), high-grade atrioventricular block, or other cardiac arrhythmias requiring anti-arrhythmic medications (except for atrial fibrillation that is well controlled with antiarrhythmic medication); history of QT interval prolongation"
            ],
            "eligibility_criteria_excerpt": "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination) Inclusion Criteria: * Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible. * Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor. * Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease * Patient must be progressing on or since most recent therapy * Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials. * ECOG performance status 0-1. * Participants must have adequate organ and marrow function as defined below: * Leukocytes >=3,000/mcL * Absolute neutrophil count >=1,50"
          }
        },
        {
          "trial_id": "NCT06625411",
          "title": "An Efficacy, Safety, and Tolerability Study of VRDN-003 in Participants With Active Thyroid Eye Disease (TED)",
          "source_url": "https://clinicaltrials.gov/study/NCT06625411",
          "retrieval_rank": 5,
          "retrieval_score": 218.991,
          "conditions": [
            "Thyroid Eye Disease"
          ],
          "phase": "PHASE3",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "VRDN-003",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06625411-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06625411-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Must have moderate to severe active TED with documented evidence of ocular symptoms or signs that began within 15 months prior to screening",
              "Must have a Clinical Activity Score (CAS) of >= 3 on the 7-item scale for the study eye",
              "Must agree to use highly effective contraception as specified in the protocol",
              "Female TED participants must have a negative serum pregnancy test at screening"
            ],
            "exclusion": [
              "Must not have received prior treatment with another anti-IGF-1R therapy",
              "Must not have received systemic corticosteroids or steroid eye drops for any condition, including TED, or selenium within 2 weeks prior to first dose",
              "Must not have received other immunosuppressive drugs for any condition, including TED, or any other therapy for TED within 12 weeks prior to first dose.",
              "Must not have received an investigational agent for any condition, including TED, within 8 weeks or longer duration (depending on the type of investigational agent) prior to first dose",
              "Must not have received radioactive iodine (RAI) treatment within 8 weeks prior to first dose",
              "Must not have had previous orbital irradiation or decompression surgery for TED to the study eye's orbit",
              "Must not have a pre-existing ophthalmic condition in the study eye which in the study doctor's opinion, would interfere with interpretation of study results",
              "Must not have abnormal hearing test before first dose. Must also not have a history of ear conditions considered significant by study doctor",
              "Must not have a history of inflammatory bowel disease",
              "Female TED participants who must not be pregnant or breastfeeding"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: * Must have moderate to severe active TED with documented evidence of ocular symptoms or signs that began within 15 months prior to screening * Must have a Clinical Activity Score (CAS) of >= 3 on the 7-item scale for the study eye * Must agree to use highly effective contraception as specified in the protocol * Female TED participants must have a negative serum pregnancy test at screening Key Exclusion Criteria: * Must not have received prior treatment with another anti-IGF-1R therapy * Must not have received systemic corticosteroids or steroid eye drops for any condition, including TED, or selenium within 2 weeks prior to first dose * Must not have received other immunosuppressive drugs for any condition, including TED, or any other therapy for TED within 12 weeks prior to first dose. * Must not have received an investigational agent for any condition, including TED, within 8 weeks or longer duration (depending on the type of investigational agent) prior to first dose * Must not have received radioactive iodine (RAI) treatment within 8 weeks prior to first dose * Must not have had previous orbital irradiation or decompression surgery for TED to the study eye's orbit * Must not have a pre-existing ophthalmic condition in the study eye which in the study doctor's opinion, would interfere with interpretation of study results * Must not have abnormal hearing test before first dose. Must also not have a history of ear conditions considered significant by study doctor * Must not have a history of inflammatory bowel disease * Female TED participants who must not be pregnant or breastfeeding NOTE: There are additional eligibility criteria for participants who do not have a meaningful response at Week 24 (irrespective of initial treatment arm) who may r"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00019",
      "patient_information_string": "Oncology referral note: SYN-GEN-00019 is a 26-year-old female with thyroid associated ophthalmopathy. Stage is recorded as IV. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in CO. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00019",
        "age": 26,
        "sex": "female",
        "diagnosis": "thyroid associated ophthalmopathy",
        "stage": "IV",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "CO"
        },
        "scenario": "exclusion_conflict",
        "target_trial_id": "NCT06392906"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT06392906",
          "title": "Orbital Radiotherapy in Grave's Ophthalmopathy 1 Week vs 2 Weeks (OraGO-1 Trial)",
          "source_url": "https://clinicaltrials.gov/study/NCT06392906",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Thyroid Associated Ophthalmopathy"
          ],
          "phase": "PHASE3",
          "status": "RECRUITING",
          "interventions": [
            "Short course radiation therapy",
            "Standard course radiation therapy"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 70,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06392906-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Associated Ophthalmopathy"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06392906-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 70
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Patient with active moderate to severe thyroid eye disease with a CAS \\> 4 with/ without diplopia before starting IVMP",
              "Patient with poor response to 3 doses of IVMP (CAS drop \\< 1) CAS score \\> 3 after 3 doses of IVMP",
              "Patients with diplopia after 3 doses of IVMP",
              "Patients with Graves' Ophthalmopathy who have maintained euthyroidism",
              "Non-pregnant adults (aged 35 years or older)"
            ],
            "exclusion": [
              "Individuals with severe hypertension or diabetic retinopathy"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Patient with active moderate to severe thyroid eye disease with a CAS \\> 4 with/ without diplopia before starting IVMP * Patient with poor response to 3 doses of IVMP (CAS drop \\< 1) CAS score \\> 3 after 3 doses of IVMP * Patients with diplopia after 3 doses of IVMP * Patients with Graves' Ophthalmopathy who have maintained euthyroidism * Non-pregnant adults (aged 35 years or older) Exclusion Criteria: * Individuals with severe hypertension or diabetic retinopathy"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 248.842,
          "conditions": [
            "Locally Advanced Bladder Urothelial Carcinoma",
            "Locally Advanced Renal Pelvis Urothelial Carcinoma",
            "Locally Advanced Ureter Urothelial Carcinoma",
            "Locally Advanced Urethral Urothelial Carcinoma",
            "Metastatic Bladder Urothelial Carcinoma",
            "Metastatic Renal Pelvis Urothelial Carcinoma",
            "Metastatic Ureter Urothelial Carcinoma",
            "Metastatic Urethral Urothelial Carcinoma",
            "Recurrent Bladder Urothelial Carcinoma",
            "Recurrent Renal Pelvis Urothelial Carcinoma",
            "Recurrent Ureter Urothelial Carcinoma",
            "Recurrent Urethral Urothelial Carcinoma",
            "Stage III Bladder Cancer AJCC v8",
            "Stage III Renal Pelvis Cancer AJCC v8",
            "Stage III Ureter Cancer AJCC v8",
            "Stage III Urethral Cancer AJCC v8",
            "Stage IV Bladder Cancer AJCC v8",
            "Stage IV Renal Pelvis Cancer AJCC v8",
            "Stage IV Ureter Cancer AJCC v8",
            "Stage IV Urethral Cancer AJCC v8",
            "Unresectable Bladder Urothelial Carcinoma",
            "Unresectable Renal Pelvis Urothelial Carcinoma",
            "Unresectable Ureter Urothelial Carcinoma",
            "Unresectable Urethral Urothelial Carcinoma"
          ],
          "phase": "PHASE2",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Atezolizumab",
            "Biopsy Procedure",
            "Biospecimen Collection",
            "Computed Tomography with Contrast",
            "Eribulin Mesylate"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 2,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03237780-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Locally Advanced Bladder Urothelial Carcinoma",
                "Locally Advanced Renal Pelvis Urothelial Carcinoma",
                "Locally Advanced Ureter Urothelial Carcinoma",
                "Locally Advanced Urethral Urothelial Carcinoma",
                "Metastatic Bladder Urothelial Carcinoma",
                "Metastatic Renal Pelvis Urothelial Carcinoma",
                "Metastatic Ureter Urothelial Carcinoma",
                "Metastatic Urethral Urothelial Carcinoma",
                "Recurrent Bladder Urothelial Carcinoma",
                "Recurrent Renal Pelvis Urothelial Carcinoma",
                "Recurrent Ureter Urothelial Carcinoma",
                "Recurrent Urethral Urothelial Carcinoma",
                "Stage III Bladder Cancer AJCC v8",
                "Stage III Renal Pelvis Cancer AJCC v8",
                "Stage III Ureter Cancer AJCC v8",
                "Stage III Urethral Cancer AJCC v8",
                "Stage IV Bladder Cancer AJCC v8",
                "Stage IV Renal Pelvis Cancer AJCC v8",
                "Stage IV Ureter Cancer AJCC v8",
                "Stage IV Urethral Cancer AJCC v8",
                "Unresectable Bladder Urothelial Carcinoma",
                "Unresectable Renal Pelvis Urothelial Carcinoma",
                "Unresectable Ureter Urothelial Carcinoma",
                "Unresectable Urethral Urothelial Carcinoma"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 2,
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study",
              "Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra",
              "Presence of measurable disease meeting the following criteria:",
              "At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm",
              "Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion",
              "Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence",
              "PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to allow for stratification; COMMERCIAL ASSESSMENT OF PD-L1 STATUS OBTAINED LOCALLY AT THE SITE WILL NOT SATISFY ELIGIBILITY CRITERIA",
              "New, progressive or recurrent disease occurring",
              "During or within 12 months of treatment with a platinum containing regimen (cisplatin or carboplatin or novel platinum) in either in the metastatic or perioperative setting",
              "In first-line patients defined as cisplatin-ineligible based on renal impairment (creatinine clearance calculated by Cockcroft-Gault method \\< 60 ml/min), at least grade 2 hearing loss and/or Eastern Cooperative Oncology Group (ECOG) status of 2; these patients will be chemotherapy naive or have received platinum based therapy in the adjuvant or neoadjuvant setting more than 12 months prior to study entry"
            ],
            "exclusion": [
              "Patients with prior allogeneic bone marrow transplantation or prior solid organ transplantation",
              "Patients who have had chemotherapy within 3 weeks or radiotherapy or targeted therapy 2 weeks (6 weeks for nitrosoureas or mitomycin C) prior to entering the study or those who have not recovered from adverse events (other than alopecia) due to agents administered more than 4 weeks earlier; however, the following therapies are allowed:",
              "Hormone-replacement therapy or oral contraceptives",
              "Herbal therapy \\> 1 week prior to cycle 1, day 1 (herbal therapy intended as anticancer therapy must be discontinued at least 1 week prior to cycle 1, day 1)",
              "Palliative radiotherapy for bone metastases \\> 2 weeks prior to cycle 1, day 1",
              "Prior treatment with anti-PD-1, or anti-PD-L1 therapeutic antibody or pathway-targeting agents or eribulin",
              "Patients who have received prior treatment with anti-CTLA-4 may be enrolled, provided the following requirements are met:",
              "Minimum of 12 weeks from the first dose of anti-CTLA-4 and \\> 6 weeks from the last dose",
              "No history of severe immune-related adverse effects from anti-CTLA-4 (National Cancer Institute \\[NCI\\] Common Terminology Criteria for Adverse Events \\[CTCAE\\] version 5.0)",
              "Treatment with any other investigational agent within 4 weeks prior to cycle 1, day 1"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study * Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra * Presence of measurable disease meeting the following criteria: * At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm * Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion * Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence * PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 3,
          "retrieval_score": 194.074,
          "conditions": [
            "Urothelial Cancer",
            "Metastatic Urothelial Carcinoma",
            "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
            "Bladder Cancer"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Sacituzumab Govitecan (SG)",
            "Enfortumab vedotin-ejfv (EV)",
            "Pembrolizumab"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04724018-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Urothelial Cancer",
                "Metastatic Urothelial Carcinoma",
                "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
                "Bladder Cancer"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination)",
              "Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible.",
              "Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor.",
              "Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease",
              "Patient must be progressing on or since most recent therapy",
              "Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials.",
              "ECOG performance status 0-1.",
              "Participants must have adequate organ and marrow function as defined below:",
              "Leukocytes >=3,000/mcL",
              "Absolute neutrophil count >=1,500/mcL"
            ],
            "exclusion": [
              "Women who are pregnant or lactating. Pregnant women are excluded from this study because SG and EV have potential for teratogenic or abortifacient effects. Because there is an unknown but potential risk for adverse events in nursing infants secondary to treatment of the mother with EV or SG, breastfeeding should be discontinued if the mother is treated on protocol.",
              "Have had a prior anti-cancer biologic agent (including immune checkpoint inhibitors) within 4 weeks prior to Cycle 1 Day 1 (C1D1) or have had prior chemotherapy, targeted small molecule therapy, or radiation therapy within 2 weeks prior to C1D1. Subjects participating in observational studies are eligible.",
              "Presence of any toxicities attributed to prior anti-cancer therapy that are not resolved to Grade 1 or baseline that could impose serious risk for complications before administration of study drug agent",
              "Note: If subjects received major surgery, they must have recovered adequately from the toxicity and/or complications from the intervention prior to starting therapy.",
              "Have previously received topoisomerase 1 inhibitors, SG or EV",
              "Have an active second malignancy. Subjects with a history of malignancy that have been completely treated, with no evidence of active cancer for 3 years prior to start of therapy on trial (Cycle 1 Day 1 \\[C1D1\\]), or subjects with surgically-cured tumors with low risk of recurrence are allowed to enroll.",
              "Have known active central nervous system (CNS) metastases and/or carcinomatous meningitis. Subjects with previously treated brain metastases may participate provided they have stable CNS disease for at least 4 weeks prior to the first dose of study drug and all neurologic symptoms have returned to baseline, have no evidence of new or enlarging brain metastases, and are taking <=20 mg/day of prednisone or its equivalent. All subjects with carcinomatous meningitis are excluded regardless of clinical stability.",
              "Have active cardiac disease, defined as:",
              "Myocardial infarction or unstable angina pectoris within 6 months prior to C1D1",
              "History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation), high-grade atrioventricular block, or other cardiac arrhythmias requiring anti-arrhythmic medications (except for atrial fibrillation that is well controlled with antiarrhythmic medication); history of QT interval prolongation"
            ],
            "eligibility_criteria_excerpt": "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination) Inclusion Criteria: * Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible. * Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor. * Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease * Patient must be progressing on or since most recent therapy * Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials. * ECOG performance status 0-1. * Participants must have adequate organ and marrow function as defined below: * Leukocytes >=3,000/mcL * Absolute neutrophil count >=1,50"
          }
        },
        {
          "trial_id": "NCT07091617",
          "title": "Testing an Enhanced Digital Delivery Model for Inherited Cancer Genetic Testing in Young Adults With Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT07091617",
          "retrieval_rank": 4,
          "retrieval_score": 186.359,
          "conditions": [
            "Miscellaneous Neoplasm, Nos",
            "Non-Neoplastic Condition, Nos"
          ],
          "phase": "NA",
          "status": "RECRUITING",
          "interventions": [
            "Telemedicine",
            "Genetic Testing",
            "Telemedicine",
            "Internet-Based Intervention",
            "Educational Intervention",
            "Patient Navigation",
            "Interview",
            "Survey Administration"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07091617-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Miscellaneous Neoplasm, Nos",
                "Non-Neoplastic Condition, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07091617-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment",
              "PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not",
              "PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish",
              "PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members",
              "PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician",
              "PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review",
              "NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial services and/or for insurance companies) who participate in oncology care among AYA in community for this study",
              "NON-PATIENT PARTICIPANT: Age >= 18 years",
              "NON-PATIENT PARTICIPANT: Non-patient participants must be able to speak and read English or Spanish in order to participate in the key informant interviews"
            ],
            "exclusion": [],
            "eligibility_criteria_excerpt": "* PATIENTS: Age >= 18 years and <= 39 years at the time of enrollment * PATIENTS: AYA cancer patients and survivors. This includes patients at any stage of diagnosis (e.g., newly diagnosed, in treatment, in survivorship) and a cancer diagnosis (including pediatric cancers) at any age <= 39 years old. Given targeted therapies for BRCA+ and microsatellite instability (MSI)-high/Lynch Syndrome patients and benefit to relatives, patients with metastatic cancer are included. Any history of cancer, regardless of being in treatment or not * PATIENTS: Language: In order to complete the mandatory patient-completed measures and receive genetic education and counseling, participants must be able to speak and read English or Spanish * PATIENTS: No known diagnosis of dementia or cognitive impairment. Persons with impaired decision-making capacity are ineligible as they need to be able to understand genetic test results, its implications for the patient and family, and explain genetic test results to their family members * PATIENTS: No persons with a known psychiatric or documented developmental disorder that affects cognitive or emotional functions to the extent that the capacity for judgment and reason is significantly diminished, such that they cannot participate based on the judgment of the treating physician * PATIENTS: Participants must meet National Comprehensive Cancer Network (NCCN) guidelines for genetic testing assessment provided by Penn Telegenetics by the Eligibility Verification Assessment (EVA) chatbot, or paper forms and genetic counselor's review * NON-PATIENT PARTICIPANT: Non-patient participants eligible for this study include: oncology providers, members of the care team and clinic staff, genetic counselors, and insurers (i.e., people who work in financial servic"
          }
        },
        {
          "trial_id": "NCT07622368",
          "title": "A Study of IBI3031 in Participants With Thyroid Eye Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT07622368",
          "retrieval_rank": 5,
          "retrieval_score": 152.674,
          "conditions": [
            "Thyroid Eye Disease"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "IBI3031",
            "placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07622368-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Thyroid Eye Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07622368-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Written informed consent.",
              "2. Aged between 18 and 75 years at screening.",
              "3. Weight between 45 kg and 100 kg.",
              "4. Moderate-to-severe active TED:",
              "CAS >= 3 in the study eye at screening and baseline;",
              "Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia;",
              "<= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening;",
              "5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2)",
              "6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening.",
              "7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening."
            ],
            "exclusion": [
              "Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible):",
              "1. The CAS of the study eye at baseline is reduced by >= 2 points compared with that at screening, or the proptosis of the study eye at baseline is reduced by >= 2 mm compared with that at screening;",
              "2. Participants previously diagnosed with dysthyroid optic neuropathy (DON), or with DON as determined by the investigator at screening;",
              "3. Patients with corneal ulcers that are not relieved after treatment at the investigator's discretion;",
              "4. Presence of other non-TED ophthalmic diseases that may affect the interpretation of study results or the safety of participants as determined by the investigator (e.g., proptosis not primarily caused by TED);",
              "5. At screening, clinical or laboratory evidence of significant hypothyroidism (presence of clinical symptoms of hypothyroidism, or FT3 or FT4 (Free Thyroxine)\\<0.5lower limit of normal \\[LLN\\], or TSH\\>1.5upper limit of normal \\[ULN\\]); or severe hyperthyroidism during the screening period (FT3 and FT4(Free Thyroxine)\\>2ULN, or presence of thyroid storm).",
              "6. Other medical history and abnormal test results during the screening period that are judged by the investigator to be clinically significant, may cause the participant to fail to comply with the study protocol or complete the trial, or endanger safety, including but not limited to:",
              "History of hepatic insufficiency (Child-Pugh Class B or C) or liver cirrhosis; aspartate aminotransferase (AST) or alanine aminotransferase (ALT) \\> 2 ULN at screening;",
              "Glomerular filtration rate (GFR) \\< 60 ml/min/1.73 m2;",
              "Poorly controlled diabetes mellitus or hypertension;"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: 1. Written informed consent. 2. Aged between 18 and 75 years at screening. 3. Weight between 45 kg and 100 kg. 4. Moderate-to-severe active TED: * CAS >= 3 in the study eye at screening and baseline; * Usually associated with at least two of the following: lid retraction >= 2 mm, moderate or severe soft tissue involvement, exophthalmos >= 3 mm above normal, and/or inconstant or constant diplopia; * <= 12 months since the onset of active TED symptoms according to subjects' chief complaint or medical record at screening; 5. Exophthalmos >= 18 mm in the study eye at baseline. (Only applicable to Stage 2) 6. Participants must be clinically and biochemically euthyroid, or have mild hypothyroidism or mild-to-moderate hyperthyroidism at screening. 7. Positive for Thyrotrophin Receptor Antibody (TRAb) at screening. 8. No prior treatment with antithyroid medications and/or thyroid hormone replacement therapy, or having taken antithyroid medications and/or thyroid hormone replacement therapy on a stable dose for at least 6 weeks prior to the first dose, or having not been treated with antithyroid medications and/or thyroid hormone replacement therapy due to intolerable side effects for at least 6 weeks prior to the first dose. 9. Infertile female participants or fertile female participants with negative blood pregnancy test results during the screening period and agree to take contraceptive measures from screening to 120 days after the last dose; male participants should agree to use contraceptive measures from screening to 120 days after the last dose. Key Exclusion Criteria: Participants to be excluded (Participants meeting any of the following criteria will be regarded as ineligible): 1. The CAS of the study eye at baseline is reduced by >= 2 points com"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00020",
      "patient_information_string": "Tumor board intake: SYN-GEN-00020 is a 74-year-old female with graves' disease. Stage is recorded as I. ECOG performance status is 1. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No uncontrolled cardiac disease is reported. No active uncontrolled infection is reported. No organ transplant is reported. The patient receives care in AZ. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00020",
        "age": 74,
        "sex": "female",
        "diagnosis": "graves' disease",
        "stage": "I",
        "ecog": 1,
        "flags": {
          "active_uncontrolled_infection": false,
          "organ_transplant": false,
          "uncontrolled_cardiac_disease": false
        },
        "location": {
          "country": "US",
          "state": "AZ"
        },
        "scenario": "stage_conflict",
        "target_trial_id": "NCT07333677"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07333677",
          "title": "In Vivo CAR-T for Refractory Graves' Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT07333677",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Graves' Disease"
          ],
          "phase": "EARLY_PHASE1",
          "status": "RECRUITING",
          "interventions": [
            "In Vivo CAR-T Therapy"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07333677-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Graves' Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07333677-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            },
            {
              "criterion_id": "NCT07333677-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07333677-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT07333677-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Age 18-75 years (inclusive), male or female.",
              "Refractory Graves' disease, defined as meeting at least one of the following: a) Continuous antithyroid drug (ATD) therapy for >=3 years without achieving criteria for ATD discontinuation; b) Meeting criteria for ATD discontinuation but experiencing >=2 relapses after ATD withdrawal.",
              "Positive serum TRAb.",
              "Willing to use effective contraception for 12 months after study drug administration.",
              "Voluntarily agrees to participate in the study, has signed the informed consent form, and is able to comply with study procedures and follow-up requirements."
            ],
            "exclusion": [
              "History of severe drug allergy or known allergic predisposition.",
              "Presence or suspected presence of uncontrolled active infection.",
              "History of major organ transplantation (e.g., heart, lung, liver, kidney) or bone marrow/hematopoietic stem cell transplantation.",
              "Presence of significant heart disease, such as angina, myocardial infarction, heart failure, or clinically significant arrhythmias.",
              "Receipt of any mRNA-LNP product or other lipid nanoparticle (LNP)-based therapy within the past 2 years.",
              "Receipt of a live vaccine within 30 days prior to screening.",
              "History of malignant tumors.",
              "Positive hepatitis B surface antigen (HBsAg) or hepatitis B core antibody (HBcAb) with peripheral blood HBV DNA above the detection limit; positive hepatitis C virus (HCV) antibody with detectable HCV RNA; positive human immunodeficiency virus (HIV) antibody; or positive syphilis test.",
              "Presence of psychiatric disorders or severe cognitive impairment.",
              "Hematologic dysfuction at screening, defined as any of the following: a. Neutrophil count \\< 1.8 10/L, b. Hemoglobin \\< 110 g/L, c. Platelet count \\< 50 10/L"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria (Participants must meet all of the following criteria to be eligible for this study): * Age 18-75 years (inclusive), male or female. * Refractory Graves' disease, defined as meeting at least one of the following: a) Continuous antithyroid drug (ATD) therapy for >=3 years without achieving criteria for ATD discontinuation; b) Meeting criteria for ATD discontinuation but experiencing >=2 relapses after ATD withdrawal. * Positive serum TRAb. * Willing to use effective contraception for 12 months after study drug administration. * Voluntarily agrees to participate in the study, has signed the informed consent form, and is able to comply with study procedures and follow-up requirements. Exclusion Criteria (Participants meeting any of the following criteria will be excluded from the study): * History of severe drug allergy or known allergic predisposition. * Presence or suspected presence of uncontrolled active infection. * History of major organ transplantation (e.g., heart, lung, liver, kidney) or bone marrow/hematopoietic stem cell transplantation. * Presence of significant heart disease, such as angina, myocardial infarction, heart failure, or clinically significant arrhythmias. * Receipt of any mRNA-LNP product or other lipid nanoparticle (LNP)-based therapy within the past 2 years. * Receipt of a live vaccine within 30 days prior to screening. * History of malignant tumors. * Positive hepatitis B surface antigen (HBsAg) or hepatitis B core antibody (HBcAb) with peripheral blood HBV DNA above the detection limit; positive hepatitis C virus (HCV) antibody with detectable HCV RNA; positive human immunodeficiency virus (HIV) antibody; or positive syphilis test. * Presence of psychiatric disorders or severe cognitive impairment. * Hematologic dysfuction at"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 2,
          "retrieval_score": 421.041,
          "conditions": [
            "Urothelial Cancer",
            "Metastatic Urothelial Carcinoma",
            "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
            "Bladder Cancer"
          ],
          "phase": "PHASE1, PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Sacituzumab Govitecan (SG)",
            "Enfortumab vedotin-ejfv (EV)",
            "Pembrolizumab"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04724018-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Urothelial Cancer",
                "Metastatic Urothelial Carcinoma",
                "Metastatic Urothelial Carcinoma of the Renal Pelvis and Ureter",
                "Bladder Cancer"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT04724018-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04724018-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination)",
              "Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible.",
              "Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor.",
              "Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease",
              "Patient must be progressing on or since most recent therapy",
              "Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials.",
              "ECOG performance status 0-1.",
              "Participants must have adequate organ and marrow function as defined below:",
              "Leukocytes >=3,000/mcL",
              "Absolute neutrophil count >=1,500/mcL"
            ],
            "exclusion": [
              "Women who are pregnant or lactating. Pregnant women are excluded from this study because SG and EV have potential for teratogenic or abortifacient effects. Because there is an unknown but potential risk for adverse events in nursing infants secondary to treatment of the mother with EV or SG, breastfeeding should be discontinued if the mother is treated on protocol.",
              "Have had a prior anti-cancer biologic agent (including immune checkpoint inhibitors) within 4 weeks prior to Cycle 1 Day 1 (C1D1) or have had prior chemotherapy, targeted small molecule therapy, or radiation therapy within 2 weeks prior to C1D1. Subjects participating in observational studies are eligible.",
              "Presence of any toxicities attributed to prior anti-cancer therapy that are not resolved to Grade 1 or baseline that could impose serious risk for complications before administration of study drug agent",
              "Note: If subjects received major surgery, they must have recovered adequately from the toxicity and/or complications from the intervention prior to starting therapy.",
              "Have previously received topoisomerase 1 inhibitors, SG or EV",
              "Have an active second malignancy. Subjects with a history of malignancy that have been completely treated, with no evidence of active cancer for 3 years prior to start of therapy on trial (Cycle 1 Day 1 \\[C1D1\\]), or subjects with surgically-cured tumors with low risk of recurrence are allowed to enroll.",
              "Have known active central nervous system (CNS) metastases and/or carcinomatous meningitis. Subjects with previously treated brain metastases may participate provided they have stable CNS disease for at least 4 weeks prior to the first dose of study drug and all neurologic symptoms have returned to baseline, have no evidence of new or enlarging brain metastases, and are taking <=20 mg/day of prednisone or its equivalent. All subjects with carcinomatous meningitis are excluded regardless of clinical stability.",
              "Have active cardiac disease, defined as:",
              "Myocardial infarction or unstable angina pectoris within 6 months prior to C1D1",
              "History of serious ventricular arrhythmia (i.e., ventricular tachycardia or ventricular fibrillation), high-grade atrioventricular block, or other cardiac arrhythmias requiring anti-arrhythmic medications (except for atrial fibrillation that is well controlled with antiarrhythmic medication); history of QT interval prolongation"
            ],
            "eligibility_criteria_excerpt": "Phase II Study Cohort A (dose expansion study to assess efficacy of Sacituzumab Govitecan (SG) and Enfortumab vedotin-ejfv (EV) combination) Inclusion Criteria: * Participants must have histologically documented confirmed predominant urothelial carcinoma (i.e. of the bladder, renal pelvis, ureter or urethra). Patients with squamous differentiation or mixed cell types are eligible if the urothelial component is more than 50%; small-cell carcinoma is not allowed. Patients with locally advanced unresectable disease are eligible. * Patient who are cisplatin eligible must have received prior treatment with platinum containing therapy defined as within the adjuvant/neoadjuvant setting with >= ypT2 disease at surgery or recurrent or progressive disease within 12 months or receiving treatment with platinum in locally advanced or metastatic setting. In addition, they must have received a checkpoint inhibitor (CPI) in locally advanced or metastatic urothelial cancer setting. Patients who received CPI therapy in the neoadjuvant/adjuvant setting and had recurrent or progressive disease either during or within 12 months of therapy completion are eligible. A CPI is defined as a PD-1 or PD-L1 inhibitor. * Patients who are cisplatin-ineligible need only have progressed on or since one line of therapy defined as therapy given in the adjuvant/neoadjuvant setting within 12 months of progression or receiving therapy for locally advanced or metastatic disease * Patient must be progressing on or since most recent therapy * Age >=18 years. Children are excluded from this study, but will be eligible for future pediatric trials. * ECOG performance status 0-1. * Participants must have adequate organ and marrow function as defined below: * Leukocytes >=3,000/mcL * Absolute neutrophil count >=1,50"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 3,
          "retrieval_score": 384.041,
          "conditions": [
            "Locally Advanced Bladder Urothelial Carcinoma",
            "Locally Advanced Renal Pelvis Urothelial Carcinoma",
            "Locally Advanced Ureter Urothelial Carcinoma",
            "Locally Advanced Urethral Urothelial Carcinoma",
            "Metastatic Bladder Urothelial Carcinoma",
            "Metastatic Renal Pelvis Urothelial Carcinoma",
            "Metastatic Ureter Urothelial Carcinoma",
            "Metastatic Urethral Urothelial Carcinoma",
            "Recurrent Bladder Urothelial Carcinoma",
            "Recurrent Renal Pelvis Urothelial Carcinoma",
            "Recurrent Ureter Urothelial Carcinoma",
            "Recurrent Urethral Urothelial Carcinoma",
            "Stage III Bladder Cancer AJCC v8",
            "Stage III Renal Pelvis Cancer AJCC v8",
            "Stage III Ureter Cancer AJCC v8",
            "Stage III Urethral Cancer AJCC v8",
            "Stage IV Bladder Cancer AJCC v8",
            "Stage IV Renal Pelvis Cancer AJCC v8",
            "Stage IV Ureter Cancer AJCC v8",
            "Stage IV Urethral Cancer AJCC v8",
            "Unresectable Bladder Urothelial Carcinoma",
            "Unresectable Renal Pelvis Urothelial Carcinoma",
            "Unresectable Ureter Urothelial Carcinoma",
            "Unresectable Urethral Urothelial Carcinoma"
          ],
          "phase": "PHASE2",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Atezolizumab",
            "Biopsy Procedure",
            "Biospecimen Collection",
            "Computed Tomography with Contrast",
            "Eribulin Mesylate"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": 2,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "platinum chemotherapy"
            ],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection",
              "organ_transplant"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03237780-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Locally Advanced Bladder Urothelial Carcinoma",
                "Locally Advanced Renal Pelvis Urothelial Carcinoma",
                "Locally Advanced Ureter Urothelial Carcinoma",
                "Locally Advanced Urethral Urothelial Carcinoma",
                "Metastatic Bladder Urothelial Carcinoma",
                "Metastatic Renal Pelvis Urothelial Carcinoma",
                "Metastatic Ureter Urothelial Carcinoma",
                "Metastatic Urethral Urothelial Carcinoma",
                "Recurrent Bladder Urothelial Carcinoma",
                "Recurrent Renal Pelvis Urothelial Carcinoma",
                "Recurrent Ureter Urothelial Carcinoma",
                "Recurrent Urethral Urothelial Carcinoma",
                "Stage III Bladder Cancer AJCC v8",
                "Stage III Renal Pelvis Cancer AJCC v8",
                "Stage III Ureter Cancer AJCC v8",
                "Stage III Urethral Cancer AJCC v8",
                "Stage IV Bladder Cancer AJCC v8",
                "Stage IV Renal Pelvis Cancer AJCC v8",
                "Stage IV Ureter Cancer AJCC v8",
                "Stage IV Urethral Cancer AJCC v8",
                "Unresectable Bladder Urothelial Carcinoma",
                "Unresectable Renal Pelvis Urothelial Carcinoma",
                "Unresectable Ureter Urothelial Carcinoma",
                "Unresectable Urethral Urothelial Carcinoma"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 2,
              "required": true
            },
            {
              "criterion_id": "NCT03237780-I-prior-platinum-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: platinum chemotherapy.",
              "structured_value": "platinum chemotherapy",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            },
            {
              "criterion_id": "NCT03237780-E-organ-transplant",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has organ transplant.",
              "structured_value": "organ_transplant",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study",
              "Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra",
              "Presence of measurable disease meeting the following criteria:",
              "At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm",
              "Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion",
              "Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence",
              "PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to allow for stratification; COMMERCIAL ASSESSMENT OF PD-L1 STATUS OBTAINED LOCALLY AT THE SITE WILL NOT SATISFY ELIGIBILITY CRITERIA",
              "New, progressive or recurrent disease occurring",
              "During or within 12 months of treatment with a platinum containing regimen (cisplatin or carboplatin or novel platinum) in either in the metastatic or perioperative setting",
              "In first-line patients defined as cisplatin-ineligible based on renal impairment (creatinine clearance calculated by Cockcroft-Gault method \\< 60 ml/min), at least grade 2 hearing loss and/or Eastern Cooperative Oncology Group (ECOG) status of 2; these patients will be chemotherapy naive or have received platinum based therapy in the adjuvant or neoadjuvant setting more than 12 months prior to study entry"
            ],
            "exclusion": [
              "Patients with prior allogeneic bone marrow transplantation or prior solid organ transplantation",
              "Patients who have had chemotherapy within 3 weeks or radiotherapy or targeted therapy 2 weeks (6 weeks for nitrosoureas or mitomycin C) prior to entering the study or those who have not recovered from adverse events (other than alopecia) due to agents administered more than 4 weeks earlier; however, the following therapies are allowed:",
              "Hormone-replacement therapy or oral contraceptives",
              "Herbal therapy \\> 1 week prior to cycle 1, day 1 (herbal therapy intended as anticancer therapy must be discontinued at least 1 week prior to cycle 1, day 1)",
              "Palliative radiotherapy for bone metastases \\> 2 weeks prior to cycle 1, day 1",
              "Prior treatment with anti-PD-1, or anti-PD-L1 therapeutic antibody or pathway-targeting agents or eribulin",
              "Patients who have received prior treatment with anti-CTLA-4 may be enrolled, provided the following requirements are met:",
              "Minimum of 12 weeks from the first dose of anti-CTLA-4 and \\> 6 weeks from the last dose",
              "No history of severe immune-related adverse effects from anti-CTLA-4 (National Cancer Institute \\[NCI\\] Common Terminology Criteria for Adverse Events \\[CTCAE\\] version 5.0)",
              "Treatment with any other investigational agent within 4 weeks prior to cycle 1, day 1"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Males or females age \\> or = 18 years at the time of informed consent. Because no dosing or adverse event data are currently available on the use of atezolizumab in combination with eribulin in patients \\< 18 years of age, children are excluded from this study * Histologically- or cytologically-confirmed diagnosis of locally advanced/unresectable (inoperable or not amenable to surgical treatment) and/or metastatic transitional cell urothelial cancer of the renal pelvis, ureter, urinary bladder, or urethra * Presence of measurable disease meeting the following criteria: * At least one lesion of \\>= 1.0 cm in long axis diameter for non-lymph nodes or \\>= 1.5 cm in short axis diameter for lymph nodes that is serially measurable according to RECIST 1.1 using either computerized tomography or magnetic resonance imaging or panoramic and close-up color photography with caliper measurement; if there is only one target lesion and it is a not a lymph node, it should have a long-axis diameter of at least 1.5 cm * Lesions that have had radiotherapy must show radiographic evidence of disease progression based on RECIST 1.1 may be deemed a target lesion * Archival paraffin-embedded invasive tumor tissue or newly obtained biopsy must be available prior to the first dose of study drug for biomarker analysis; patients must be offered sequential biopsies at baseline and 6 weeks unless in the opinion of the trial principal investigator (PI) this would be hazardous; recent data suggest discordance between primary tumor and tumor from recurrence or metastasis with high percentages of PD-L1 SP142 positive immune cells after recurrence * PD-L1 status determined centrally by HistogeneX, which is funded by the study, must be available before randomization of the patient to"
          }
        },
        {
          "trial_id": "NCT06830031",
          "title": "Clinical Study of C402-CD19-CAR Treatment in Subjects With Relapsed or Refractory B-cell Lymphoma",
          "source_url": "https://clinicaltrials.gov/study/NCT06830031",
          "retrieval_rank": 4,
          "retrieval_score": 247.453,
          "conditions": [
            "Diffuse Large B-cell-lymphoma",
            "DLBCL, Nos Genetic Subtypes",
            "Follicular Lymphoma Grade 3B",
            "PMBL",
            "HGBL With MYC and BCL2 and/or BCL6 Rearrangements",
            "HGBL, Nos"
          ],
          "phase": "PHASE1",
          "status": "RECRUITING",
          "interventions": [
            "C402-CD19-CAR"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 75,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": 1,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06830031-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Diffuse Large B-cell-lymphoma",
                "DLBCL, Nos Genetic Subtypes",
                "Follicular Lymphoma Grade 3B",
                "PMBL",
                "HGBL With MYC and BCL2 and/or BCL6 Rearrangements",
                "HGBL, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06830031-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            },
            {
              "criterion_id": "NCT06830031-I-ecog",
              "criterion_type": "inclusion",
              "criterion": "Patient ECOG performance status should be at or below the maximum.",
              "structured_value": 1,
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT06830031-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Male or female 18-75 years (inclusive);",
              "2. Patients can understand this study and capable of providing informed consent;",
              "3. Patients with willingness to be in the study and comply with the study visit procedures and other protocol requirements;",
              "4. Diagnosed with CD19-positive large B-cell lymphoma (LBCL) based on cytology or histology according to the WHO 2016 standards, including diffuse large B-cell lymphoma not otherwise specified (DLBCL-NOS), grade 3b follicular lymphoma (FL), transformed diffuse large B-cell lymphoma, primary mediastinal B-cell lymphoma (PMBL), high-grade B-cell lymphoma (HGBL) with MYC, BCL-2, and/or BCL-6 rearrangements, and high-grade B-cell lymphoma not otherwise specified (HGBL-NOS). For CD19 expression status, subjects with a clear past record of tumor histological diagnosis as CD19-positive (within 6 months prior to screening with no CD19-related treatment in the last 6 months) and tumors showing CD19-positive lymphoma levels >= 50% by IHC or CD19-positive lymphoma levels >= 70% by flow cytometry. If there is no previous CD19 tumor testing or the result is over 6 months prior to screening, a new tumor pathology sample must be provided or re-collected for CD19-positive diagnosis by the institution, with IHC showing CD19-positive lymphoma levels >= 50% or flow cytometry showing CD19-positive lymphoma levels >= 70%.",
              "5. For refractory or relapsed large B-cell lymphoma subjects, must have received at least anthracycline-based therapy and rituximab (or other CD20-targeted drugs, excluding CD20-negative cases). If previously treated with R-CHOP or other CD20-targeted therapy, the best treatment outcome prior to relapse must have been complete remission (CR). Subjects should meet the criteria for relapse, progression, or failure after second-line therapy; or relapse after autologous hematopoietic stem cell transplantation (auto-HSCT). If the subject has undergone previous auto-HSCT, the best treatment outcome prior to relapse must have been CR, and the relapse should occur more than 12 months after the previous treatment. (Refractory is defined as the best response to the most recent treatment being disease progression or stable disease after at least 2 cycles of the last-line therapy).",
              "6. According to the 2014 Lugano Treatment Response Assessment Criteria, at least one measurable tumor lesion should be present (lesions can be measured with PET results; lymph node lesions \\[long axis LDi \\> 15mm\\] or extra nodal lesions \\[long axis LDi \\> 10mm\\]);",
              "7. Expected survival time greater than 12 weeks;",
              "8. ECOG score of 0-1;",
              "9. Able to establish an intravenous route for PBMC collection, meeting the following hematologic parameters before screening: Hemoglobin >= 80 g/L, absolute neutrophil count >= 1.0 10\\^9/L, platelet count >= 75 10\\^9/L, lymphocyte count >= 0.5 10\\^9/L (if using bone marrow stimulants or blood transfusion, a washout period of 7 days is required; for granulocyte colony-stimulating factor \\[G-CSF\\] or granulocyte-macrophage colony-stimulating factor \\[GM-CSF\\], a washout period of 4 weeks or 5 half-lives is required);",
              "10. Liver and kidney function, as well as heart and lung function, should meet the following requirements:"
            ],
            "exclusion": [
              "1. History of receiving allogeneic hematopoietic stem cell transplantation, adoptive cell therapy (such as CAR-T therapy), or other gene-modified cell therapies;",
              "2. Any active central nervous system (CNS) involvement (including symptomatic and asymptomatic), or a history of CNS disease (such as epilepsy, cerebral ischemia/hemorrhage, dementia, cerebellar disorders, or any autoimmune diseases involving the CNS);",
              "3. Positive for hepatitis B surface antigen (HBsAg) or hepatitis B core antibody (HBcAb) with peripheral blood HBV DNA positivity, or subjects with HBV titers above the upper limit of the normal range for the study center; positive for hepatitis C virus (HCV) antibody and peripheral blood HCV RNA positivity; positive for cytomegalovirus (CMV) DNA; positive for human immunodeficiency virus (HIV) antibody; positive for syphilis test;",
              "4. Any unstable systemic disease, including but not limited to unstable angina, cerebrovascular accident or transient ischemic attack (within 6 months prior to screening), myocardial infarction (within 6 months prior to screening), congestive heart failure (New York Heart Association \\[NYHA\\] classification >= III), active bleeding, severe arrhythmias requiring drug treatment, liver, kidney, or metabolic disorders;",
              "5. Presence of malignant tumors other than large B-cell lymphoma, except for cured non-melanoma skin cancer, carcinoma in situ of the cervix, localized prostate cancer, superficial bladder cancer, ductal carcinoma in situ, and other cancers with a disease-free survival of more than 5 years;",
              "6. Presence of gastric lymphoma, bulky disease, a history of CD19+ leukemia, or active autoimmune diseases (e.g., systemic lupus erythematosus, Sjgren's syndrome, rheumatoid arthritis, psoriasis, multiple sclerosis, inflammatory bowel disease, Hashimoto's thyroiditis, etc.);",
              "7. Presence of uncontrolled active infections requiring treatment (e.g., sepsis, bacteremia, fungemia, viremia) (mild urinary tract infections or upper respiratory tract infections are exceptions), with the exception of prophylactic anti-infection treatment (for bacterial, fungal, viral infections, etc.);",
              "8. Subjects who have received systemic steroid treatment within 2 weeks before PBMC collection and are determined by the investigator to require long-term systemic steroid treatment during the treatment period (except for inhaled, local application, or physiological replacement doses \\[hydrocortisone <=7 mgd-1 or equivalent prednisone <=5 mgd-1 or dexamethasone <=0.5 mgd-1\\]);",
              "9. Subjects who have received anti-tumor treatment within 8 weeks or 5 half-lives (specific medications need to be assessed in detail) before PBMC collection, including chemotherapy, CD20-targeted therapy, etc.; local radiotherapy within 12 weeks;",
              "10. Subjects who have used granulocyte colony-stimulating factor (G-CSF) or granulocyte-macrophage colony-stimulating factor (GM-CSF) within 4 weeks before PBMC collection or within at least 5 half-lives (whichever is shorter);"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: Must meet all the following inclusion criteria: 1. Male or female 18-75 years (inclusive); 2. Patients can understand this study and capable of providing informed consent; 3. Patients with willingness to be in the study and comply with the study visit procedures and other protocol requirements; 4. Diagnosed with CD19-positive large B-cell lymphoma (LBCL) based on cytology or histology according to the WHO 2016 standards, including diffuse large B-cell lymphoma not otherwise specified (DLBCL-NOS), grade 3b follicular lymphoma (FL), transformed diffuse large B-cell lymphoma, primary mediastinal B-cell lymphoma (PMBL), high-grade B-cell lymphoma (HGBL) with MYC, BCL-2, and/or BCL-6 rearrangements, and high-grade B-cell lymphoma not otherwise specified (HGBL-NOS). For CD19 expression status, subjects with a clear past record of tumor histological diagnosis as CD19-positive (within 6 months prior to screening with no CD19-related treatment in the last 6 months) and tumors showing CD19-positive lymphoma levels >= 50% by IHC or CD19-positive lymphoma levels >= 70% by flow cytometry. If there is no previous CD19 tumor testing or the result is over 6 months prior to screening, a new tumor pathology sample must be provided or re-collected for CD19-positive diagnosis by the institution, with IHC showing CD19-positive lymphoma levels >= 50% or flow cytometry showing CD19-positive lymphoma levels >= 70%. 5. For refractory or relapsed large B-cell lymphoma subjects, must have received at least anthracycline-based therapy and rituximab (or other CD20-targeted drugs, excluding CD20-negative cases). If previously treated with R-CHOP or other CD20-targeted therapy, the best treatment outcome prior to relapse must have been complete remission (CR). Subjects should meet"
          }
        },
        {
          "trial_id": "NCT06942039",
          "title": "Pilot Study of IT Topotecan and Maintenance Chemotherapy for HR-EBTs in Children < 6 Years, Post Consolidation",
          "source_url": "https://clinicaltrials.gov/study/NCT06942039",
          "retrieval_rank": 5,
          "retrieval_score": 213.058,
          "conditions": [
            "CNS Embryonal Tumor",
            "CNS, Medulloblastoma",
            "Atypical Teratoid Rhabdoid Tumor",
            "Medulloblastoma, Childhood",
            "Medulloblastoma, Group 3",
            "Medulloblastoma, Group 4",
            "Pineoblastoma",
            "Neuroblastoma",
            "Embryonal Tumor With Multilayered Rosettes",
            "Embryonal Tumor With Abundant Neuropil and True Rosettes",
            "Ependymoblastoma",
            "Medulloepithelioma",
            "CNS Embryonal Tumor With Rhabdoid Features",
            "CNS Embryonal Tumor, Nos"
          ],
          "phase": "EARLY_PHASE1",
          "status": "RECRUITING",
          "interventions": [
            "Cytarabine IT",
            "hydrocortisone",
            "Cisplatin",
            "Vincristine",
            "Etoposide",
            "Cyclophosphamide",
            "Mesna",
            "Filgrastim"
          ],
          "known_structured_fields": {
            "min_age": null,
            "max_age": 6,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "uncontrolled_cardiac_disease",
              "active_uncontrolled_infection"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06942039-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "CNS Embryonal Tumor",
                "CNS, Medulloblastoma",
                "Atypical Teratoid Rhabdoid Tumor",
                "Medulloblastoma, Childhood",
                "Medulloblastoma, Group 3",
                "Medulloblastoma, Group 4",
                "Pineoblastoma",
                "Neuroblastoma",
                "Embryonal Tumor With Multilayered Rosettes",
                "Embryonal Tumor With Abundant Neuropil and True Rosettes",
                "Ependymoblastoma",
                "Medulloepithelioma",
                "CNS Embryonal Tumor With Rhabdoid Features",
                "CNS Embryonal Tumor, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06942039-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": null,
                "max_age": 6
              },
              "required": true
            },
            {
              "criterion_id": "NCT06942039-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06942039-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            },
            {
              "criterion_id": "NCT06942039-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. Tumor Tissue Sample",
              "2. Age: Patient must be aged >= 0 years to <= 6 years at the time of definitive confirmation of histologic diagnosis of eligible CNS tumor.",
              "3. Diagnoses. Participants must have Central nervous system (CNS) HR-EBT including atypical teratoid rhabdoid tumour (ATRT), group 3 and group 4 medulloblastoma (MB), pineoblastoma, CNS neuroblastoma, embryonal tumor with multi-layered rosettes (ETMR including embryonal tumor with abundant neuropil and true rosettes (ETANTR), ependymoblastoma and ETMR not otherwise specified), medulloepithelioma, CNS embryonal tumor with rhabdoid features (INI-1 intact) and CNS embryonal tumor, not otherwise specified. Metastatic disease included. Any extent of resection included.",
              "4. Cranial and Spine MRI. A baseline MRI brain and spine with and without contrast is required for all patients. cranial MRI (with and without gadolinium) must be done pre-operatively. Post-operatively, cranial MRI (with and without gadolinium) must be done.",
              "5. Lumbar Puncture (LP) CSF for cytopathology (strongly recommended but not mandatory; if medically feasible). A baseline LP CSF cytology either pre-operatively or post-operatively at least 10 days after definitive surgery for all patients if medically feasible (This is not mandatory and will not make the patient ineligible).",
              "6. Life expectancy: Patients must have a life expectancy of greater than 8 weeks from diagnosis.",
              "7. Performance level: Patients must have a performance status corresponding of a Lansky score >= 50.",
              "8. Organ Function Requirements: Participants must have normal organ and marrow function as defined below:",
              "Adequate renal function defined as:",
              "\\- Creatinine clearance (12-24-hour urine collection) or radioisotope glomerular filtration rate (GFR) >= 60 ml/min/1.73m2"
            ],
            "exclusion": [
              "1. Patients who are receiving any other conventional anti-cancer agents or investigational agents.",
              "2. Patients who received previous therapy including radiotherapy or chemotherapy other than corticosteroids.",
              "3. Presence of another malignancy, except if the other primary malignancy is neither currently clinically significant nor requiring active intervention.",
              "4. Concomitant medications restrictions: Concurrent use of enzyme inducing anticonvulsants (e.g. phenytoin, phenobarbital, and carbamazepine), selected strong inhibitors of cytochrome P450 3A4 include azole antifungals, such as fluconazole, voriconazole, itraconazole, ketoconazole, and strong inducers include drugs such as rifampin, phenytoin, phenobarbitol, carbamazepine, and St. John's wort or CYP450 3A4 stimulators or inhibitors.",
              "5. Other uncontrollable medical disease: Patient has a severe and uncontrollable medical disease (i.e., uncontrolled diabetes, hyperglycemia, chronic renal disease or active uncontrolled infection), has chronic liver disease (i.e., chronic active hepatitis and cirrhosis), hypercholesterolemia (serum cholesterol \\>300 mg/dL), intercurrent illness including, but not limited to, ongoing or active infection, symptomatic congestive heart failure, unstable angina pectoris, cardiac arrhythmia, active hyperparathyroidism, or psychiatric illness/social situations that would limit compliance with study requirements.",
              "6. Patients who have a known diagnosis of human immunodeficiency virus (HIV) infection, hepatitis B or C.",
              "7. Ineligible diagnoses for study entry by neuropathology: This includes sonic hedgehog (SHH) and wingless (WNT) MBs, all ependymomas, all choroid plexus carcinomas, all high grade glial and glio-neuronal tumors, all diffuse midline gliomas, all primary CNS germ cell tumors, all primary CNS sarcomas, all primary or metastatic CNS lymphomas and solid leukemic lesions (chloromas, granulocytic sarcomas).",
              "8. The participant or parent(s)/guardian(s) cannot comply with the study visit schedule and other protocol requirements, in the investigator's opinion."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1. Tumor Tissue Sample 2. Age: Patient must be aged >= 0 years to <= 6 years at the time of definitive confirmation of histologic diagnosis of eligible CNS tumor. 3. Diagnoses. Participants must have Central nervous system (CNS) HR-EBT including atypical teratoid rhabdoid tumour (ATRT), group 3 and group 4 medulloblastoma (MB), pineoblastoma, CNS neuroblastoma, embryonal tumor with multi-layered rosettes (ETMR including embryonal tumor with abundant neuropil and true rosettes (ETANTR), ependymoblastoma and ETMR not otherwise specified), medulloepithelioma, CNS embryonal tumor with rhabdoid features (INI-1 intact) and CNS embryonal tumor, not otherwise specified. Metastatic disease included. Any extent of resection included. 4. Cranial and Spine MRI. A baseline MRI brain and spine with and without contrast is required for all patients. cranial MRI (with and without gadolinium) must be done pre-operatively. Post-operatively, cranial MRI (with and without gadolinium) must be done. 5. Lumbar Puncture (LP) CSF for cytopathology (strongly recommended but not mandatory; if medically feasible). A baseline LP CSF cytology either pre-operatively or post-operatively at least 10 days after definitive surgery for all patients if medically feasible (This is not mandatory and will not make the patient ineligible). 6. Life expectancy: Patients must have a life expectancy of greater than 8 weeks from diagnosis. 7. Performance level: Patients must have a performance status corresponding of a Lansky score >= 50. 8. Organ Function Requirements: Participants must have normal organ and marrow function as defined below: Adequate renal function defined as: \\- Creatinine clearance (12-24-hour urine collection) or radioisotope glomerular filtration rate (GFR) >= 60 ml/min/1.7"
          }
        }
      ]
    }
  ]
}
