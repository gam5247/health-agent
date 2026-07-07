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
  "batch_id": "gpt_e2e_teacher_batch_18",
  "patients": [
    {
      "patient_id": "SYN-GEN-00086",
      "patient_information_string": "Tumor board intake: SYN-GEN-00086 is a 80-year-old male with relapsed acute myeloid leukemia. Stage is recorded as III. ECOG performance status is 1. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No active interstitial lung disease is reported. The patient receives care in IL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00086",
        "age": 80,
        "sex": "male",
        "diagnosis": "relapsed acute myeloid leukemia",
        "stage": "III",
        "ecog": 1,
        "flags": {
          "active_interstitial_lung_disease": false
        },
        "location": {
          "country": "US",
          "state": "IL"
        },
        "scenario": "wrong_condition",
        "target_trial_id": "NCT03297775"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT03297775",
          "title": "Rheumatoid Arthritis Patients at Risk for Interstitial Lung Disease",
          "source_url": "https://clinicaltrials.gov/study/NCT03297775",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Rheumatoid Arthritis",
            "Interstitial Lung Disease"
          ],
          "phase": null,
          "status": "RECRUITING",
          "interventions": [],
          "known_structured_fields": {
            "min_age": 45,
            "max_age": 90,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT03297775-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Rheumatoid Arthritis",
                "Interstitial Lung Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT03297775-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 45,
                "max_age": 90
              },
              "required": true
            },
            {
              "criterion_id": "NCT03297775-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. >= 45years old",
              "2. Diagnosis of RA using the 2010 American College of Rheumatology (ACR) criteria"
            ],
            "exclusion": [
              "1. Inability to give informed consent",
              "2. Pregnant women",
              "3. History of interstitial lung disease",
              "4. Evidence of other causes of diffuse parenchymal lung disease such as infection, drug toxicity, other autoimmune processes, etc.",
              "5. Subjects over the age of 90 years old or less than 45 years old"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1. >= 45years old 2. Diagnosis of RA using the 2010 American College of Rheumatology (ACR) criteria Exclusion Criteria: 1. Inability to give informed consent 2. Pregnant women 3. History of interstitial lung disease 4. Evidence of other causes of diffuse parenchymal lung disease such as infection, drug toxicity, other autoimmune processes, etc. 5. Subjects over the age of 90 years old or less than 45 years old"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 331.358,
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
          "retrieval_score": 282.748,
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
          "retrieval_score": 265.577,
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
          "trial_id": "NCT04262167",
          "title": "Human Autologous Lung Stem Cell Transplant for Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT04262167",
          "retrieval_rank": 5,
          "retrieval_score": 223.062,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
          ],
          "phase": "PHASE1",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Lung Spheroid Stem Cells 100 million",
            "Lung Spheroid Stem Cells 200 million"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": 80,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04262167-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04262167-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": 80
              },
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Male or female between the ages of 40 to 80.",
              "Diagnosis of a Progressive Fibrotic Interstitial Lung Disease",
              "Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF:",
              "1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded.",
              "2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded.",
              "Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening).",
              "Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity.",
              "Ability to perform a 6-Minute Walk Test (6MWT) at screening.",
              "Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures"
            ],
            "exclusion": [
              "Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease.",
              "Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge.",
              "Evidence of sustained improvement lung function defined as improvement from pre-therapy pulmonary function tests (PFTs) observed with two or more successive post-therapy PFTs over the year prior to randomization.",
              "Active or recent (less than 60 days prior to enrollment) significant respiratory tract infections, or a history of frequent (greater than 2 per year for the last 2 years) infective exacerbations of IPF.",
              "Hospitalization within 60 days of screening for an acute exacerbation of IPF (AE-IPF).",
              "Chronic heart failure (NYHA class III/IV) or known left ventricular ejection fraction less than 45%.",
              "Acute or chronic impairment (other than dyspnea) which limits the ability to comply with study requirements and procedures including the 6MWT.",
              "Subject requires hemodialysis, peritoneal dialysis or hemofiltration.",
              "Infection with HIV",
              "Viral Hepatitis"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Male or female between the ages of 40 to 80. * Diagnosis of a Progressive Fibrotic Interstitial Lung Disease * Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF: 1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded. 2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded. * Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening). * Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity. * Ability to perform a 6-Minute Walk Test (6MWT) at screening. * Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures Exclusion Criteria: * Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease. * Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge. * Evidence of sustained improvement lung function defined as improvement from"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00087",
      "patient_information_string": "Oncology referral note: SYN-GEN-00087 is a 46-year-old female with idiopathic pulmonary fibrosis(ipf). Stage is recorded as III. ECOG performance status is not documented. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No active interstitial lung disease is reported. No active uncontrolled infection is reported. The patient receives care in FL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00087",
        "age": 46,
        "sex": "female",
        "diagnosis": "idiopathic pulmonary fibrosis(ipf)",
        "stage": "III",
        "flags": {
          "active_interstitial_lung_disease": false,
          "active_uncontrolled_infection": false
        },
        "location": {
          "country": "US",
          "state": "FL"
        },
        "scenario": "missing_ecog",
        "target_trial_id": "NCT07329959"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07329959",
          "title": "CAR-DC for End-Stage IPF",
          "source_url": "https://clinicaltrials.gov/study/NCT07329959",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis(IPF)"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "Leukapheresis",
            "CAR-DC"
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
              "active_interstitial_lung_disease",
              "active_uncontrolled_infection"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07329959-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis(IPF)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07329959-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            },
            {
              "criterion_id": "NCT07329959-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07329959-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1\\. Aged between 18 and 75 years, inclusive, with a diagnosis of idiopathic pulmonary fibrosis (IPF).",
              "2\\. Ability to verbally confirm understanding of the risks, benefits, and alternative treatments associated with immunosuppressive CAR-DC therapy. Provision of written informed consent by the patient or their legally authorized representative prior to participation.",
              "3\\. Evidence of disease progression (worsening pulmonary fibrosis and declining lung function) despite treatment with standard therapies such as pirfenidone, nintedanib, or other appropriate regimens.",
              "4\\. Meets at least one criterion indicating eligibility for lung transplantation due to interstitial lung disease, while not consenting to a transplant. The criteria include:",
              "1. A decline in forced vital capacity (FVC) >=10% over a 6-month follow-up period.",
              "2. A decline in diffusing capacity of the lungs for carbon monoxide (DLCO) >=10% of predicted value over 6 months.",
              "3. Six-minute walk test results showing oxygen saturation \\<88%, a distance walked \\<250 meters, or a decline of \\>50 meters in distance over 6 months.",
              "4. Presence of pulmonary hypertension (PH) confirmed by right heart catheterization or transthoracic echocardiography.",
              "5. Hospitalization due to respiratory functional decline, pneumothorax, or acute exacerbation.",
              "5\\. No prior cellular immunotherapy within the last 3 months. 6. Hematological parameters meeting the following thresholds: hematocrit \\>30%, lymphocyte count \\>0.5 10/L, and platelet count \\>60 10/L."
            ],
            "exclusion": [
              "1. History of acute exacerbation of IPF within 4 weeks prior to screening or during the screening period.",
              "2. Presence of interstitial lung disease (ILD) other than IPF, including but not limited to: other forms of idiopathic interstitial pneumonia; ILD associated with fibrogenic agents, environmental exposures, or drug toxicity; other occupational lung diseases; granulomatous lung diseases; pulmonary vascular diseases; or ILD related to systemic diseases (e.g., vasculitis, infections such as tuberculosis, connective tissue diseases). Cases with uncertain diagnosis require serological testing and/or multidisciplinary team review for confirmation.",
              "3. Presence of significant active infection.",
              "4. History of malignancy, except for malignancies treated with curative intent and with no recurrence for >=5 years, resected basal cell or squamous cell skin carcinoma, carcinoma in situ of the cervix, or resected colonic polyps.",
              "5. Significant history of infectious diseases.",
              "6. Presence of psychiatric illness or other conditions that would compromise the patient's ability to cooperate with study requirements, comply with treatment, or undergo monitoring.",
              "7. Known hypersensitivity to any component of the immunosuppressive CAR-DC cell product.",
              "8. History of severe renal failure requiring renal dialysis, or serum creatinine level \\>2.5 mg/dL.",
              "9. Any contraindication to the investigational product or study procedures.",
              "10. Pregnancy or lactation."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1\\. Aged between 18 and 75 years, inclusive, with a diagnosis of idiopathic pulmonary fibrosis (IPF). 2\\. Ability to verbally confirm understanding of the risks, benefits, and alternative treatments associated with immunosuppressive CAR-DC therapy. Provision of written informed consent by the patient or their legally authorized representative prior to participation. 3\\. Evidence of disease progression (worsening pulmonary fibrosis and declining lung function) despite treatment with standard therapies such as pirfenidone, nintedanib, or other appropriate regimens. 4\\. Meets at least one criterion indicating eligibility for lung transplantation due to interstitial lung disease, while not consenting to a transplant. The criteria include: 1. A decline in forced vital capacity (FVC) >=10% over a 6-month follow-up period. 2. A decline in diffusing capacity of the lungs for carbon monoxide (DLCO) >=10% of predicted value over 6 months. 3. Six-minute walk test results showing oxygen saturation \\<88%, a distance walked \\<250 meters, or a decline of \\>50 meters in distance over 6 months. 4. Presence of pulmonary hypertension (PH) confirmed by right heart catheterization or transthoracic echocardiography. 5. Hospitalization due to respiratory functional decline, pneumothorax, or acute exacerbation. 5\\. No prior cellular immunotherapy within the last 3 months. 6. Hematological parameters meeting the following thresholds: hematocrit \\>30%, lymphocyte count \\>0.5 10/L, and platelet count \\>60 10/L. Exclusion Criteria: 1. History of acute exacerbation of IPF within 4 weeks prior to screening or during the screening period. 2. Presence of interstitial lung disease (ILD) other than IPF, including but not limited to: other forms of idiopathic interstitial pneumonia; I"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 2,
          "retrieval_score": 389.929,
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
          "trial_id": "NCT07447102",
          "title": "Phase II Clinical Study of BC006 in Patients With Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT07447102",
          "retrieval_rank": 3,
          "retrieval_score": 371.07,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis (IPF)"
          ],
          "phase": "PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "BC006",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07447102-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis (IPF)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07447102-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation.",
              "Aged >=40 years at the time of signing the ICF, with no gender restriction.",
              "Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline.",
              "HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available.",
              "Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period.",
              "Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period.",
              "Meets either of the following:",
              "The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study.",
              "The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should discontinue approved therapy to participate in this study. Treatment-nave patients must decline after full discussion with the investigator regarding the risks/benefits of such therapy.",
              "Patients of reproductive potential (male and female) must agree to use highly effective contraceptive methods (hormonal, barrier, or abstinence) from signing the ICF until at least 6 months after the last dose of study drug."
            ],
            "exclusion": [
              "Interstitial lung disease of known etiology (e.g., domestic and occupational environmental exposures, connective tissue disease, drug toxicity, etc.).",
              "Other pulmonary diseases considered clinically significant by the investigator (e.g., asthma, chronic obstructive pulmonary disease, cavitary or pleural disease, etc.).",
              "Emphysema >= 50%, or emphysema greater than fibrosis, as determined by independent central imaging review of HRCT.",
              "Acute exacerbation of IPF within 3 months prior to screening or during the screening period, as judged by the investigator.",
              "Sustained improvement in IPF severity within 12 months prior to screening or during the screening period, as judged by the investigator based on changes in FVC, DLCO, and/or chest HRCT scan.",
              "Pre-bronchodilator forced expiratory volume in 1 second (FEV1)/FVC \\< 0.70 during the screening period.",
              "Known increase in FEV1 and/or FVC >= 12% and >= 200 mL post-bronchodilator.",
              "History of smoking within 3 months prior to screening or during the screening period, or inability to refrain from smoking (including cigarettes, cigars, pipes, and e-cigarettes) for the duration of the study.",
              "Completed a cardiopulmonary rehabilitation program focusing on exercise training within 8 weeks prior to screening, or planning to initiate such a program during the study.",
              "Presence of pulmonary hypertension or cor pulmonale that, in the investigator's opinion, would significantly limit compliance with study requirements or may affect assessment of study safety or efficacy."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation. * Aged >=40 years at the time of signing the ICF, with no gender restriction. * Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline. * HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available. * Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period. * Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period. * Meets either of the following: * The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study. * The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should disco"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 4,
          "retrieval_score": 361.624,
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
          "trial_id": "NCT04262167",
          "title": "Human Autologous Lung Stem Cell Transplant for Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT04262167",
          "retrieval_rank": 5,
          "retrieval_score": 351.661,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
          ],
          "phase": "PHASE1",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Lung Spheroid Stem Cells 100 million",
            "Lung Spheroid Stem Cells 200 million"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": 80,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04262167-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04262167-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": 80
              },
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Male or female between the ages of 40 to 80.",
              "Diagnosis of a Progressive Fibrotic Interstitial Lung Disease",
              "Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF:",
              "1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded.",
              "2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded.",
              "Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening).",
              "Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity.",
              "Ability to perform a 6-Minute Walk Test (6MWT) at screening.",
              "Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures"
            ],
            "exclusion": [
              "Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease.",
              "Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge.",
              "Evidence of sustained improvement lung function defined as improvement from pre-therapy pulmonary function tests (PFTs) observed with two or more successive post-therapy PFTs over the year prior to randomization.",
              "Active or recent (less than 60 days prior to enrollment) significant respiratory tract infections, or a history of frequent (greater than 2 per year for the last 2 years) infective exacerbations of IPF.",
              "Hospitalization within 60 days of screening for an acute exacerbation of IPF (AE-IPF).",
              "Chronic heart failure (NYHA class III/IV) or known left ventricular ejection fraction less than 45%.",
              "Acute or chronic impairment (other than dyspnea) which limits the ability to comply with study requirements and procedures including the 6MWT.",
              "Subject requires hemodialysis, peritoneal dialysis or hemofiltration.",
              "Infection with HIV",
              "Viral Hepatitis"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Male or female between the ages of 40 to 80. * Diagnosis of a Progressive Fibrotic Interstitial Lung Disease * Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF: 1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded. 2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded. * Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening). * Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity. * Ability to perform a 6-Minute Walk Test (6MWT) at screening. * Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures Exclusion Criteria: * Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease. * Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge. * Evidence of sustained improvement lung function defined as improvement from"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00088",
      "patient_information_string": "Tumor board intake: SYN-GEN-00088 is a 67-year-old male with idiopathic pulmonary fibrosis (ipf). Stage is recorded as III. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No active interstitial lung disease is reported. The patient receives care in PA. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00088",
        "age": 67,
        "sex": "male",
        "diagnosis": "idiopathic pulmonary fibrosis (ipf)",
        "stage": "III",
        "ecog": 0,
        "flags": {
          "active_interstitial_lung_disease": false
        },
        "location": {
          "country": "US",
          "state": "PA"
        },
        "scenario": "prior_treatment_gap",
        "target_trial_id": "NCT07613216"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07613216",
          "title": "A Comparison of a Medication Adherence Platform (FORTISKAP) vs. Usual Care in Subjects on Oral Medications for the Treatment of Interstitial Lung Disease, Sarcoid and Pulmonary Hypertension",
          "source_url": "https://clinicaltrials.gov/study/NCT07613216",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis (IPF)",
            "Sarcoidosis Lung",
            "Pulmonary Hypertension",
            "Usual Interstitial Pneumonia"
          ],
          "phase": null,
          "status": "NOT_YET_RECRUITING",
          "interventions": [],
          "known_structured_fields": {
            "min_age": 21,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07613216-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis (IPF)",
                "Sarcoidosis Lung",
                "Pulmonary Hypertension",
                "Usual Interstitial Pneumonia"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07613216-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 21,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07613216-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1. 21 years of age or older at time of enrollment",
              "2. Primary diagnosis of interstitial lung disease (including sarcoidosis) AND/OR pulmonary hypertension",
              "3. Currently managing their oral medications independently (i.e., without requiring caregiver administration)",
              "4. At least one oral medication with a primary indication for treatment of ILD or PH already in use, or planned for initiation with insurance approval secured, at the time of enrollment",
              "5. 6-Minute Walk Test (6MWT) scheduled within the next 30 days or performed within the past 30 days",
              "6. For ILD subjects: FVC and/or DLCO scheduled within the next 30 days or performed within the past 90 days",
              "7. For PH subjects: Cardiac echocardiography scheduled within the next 30 days or performed within the past 90 days",
              "8. Daily access to a smartphone compatible with the FORTISKAP companion application",
              "9. Proficient in English"
            ],
            "exclusion": [],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1. 21 years of age or older at time of enrollment 2. Primary diagnosis of interstitial lung disease (including sarcoidosis) AND/OR pulmonary hypertension 3. Currently managing their oral medications independently (i.e., without requiring caregiver administration) 4. At least one oral medication with a primary indication for treatment of ILD or PH already in use, or planned for initiation with insurance approval secured, at the time of enrollment 5. 6-Minute Walk Test (6MWT) scheduled within the next 30 days or performed within the past 30 days 6. For ILD subjects: FVC and/or DLCO scheduled within the next 30 days or performed within the past 90 days 7. For PH subjects: Cardiac echocardiography scheduled within the next 30 days or performed within the past 90 days 8. Daily access to a smartphone compatible with the FORTISKAP companion application 9. Proficient in English Exclusion Criteria: Failure to meet any one of the above inclusion criteria"
          }
        },
        {
          "trial_id": "NCT07447102",
          "title": "Phase II Clinical Study of BC006 in Patients With Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT07447102",
          "retrieval_rank": 2,
          "retrieval_score": 342.118,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis (IPF)"
          ],
          "phase": "PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "BC006",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07447102-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis (IPF)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07447102-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation.",
              "Aged >=40 years at the time of signing the ICF, with no gender restriction.",
              "Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline.",
              "HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available.",
              "Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period.",
              "Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period.",
              "Meets either of the following:",
              "The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study.",
              "The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should discontinue approved therapy to participate in this study. Treatment-nave patients must decline after full discussion with the investigator regarding the risks/benefits of such therapy.",
              "Patients of reproductive potential (male and female) must agree to use highly effective contraceptive methods (hormonal, barrier, or abstinence) from signing the ICF until at least 6 months after the last dose of study drug."
            ],
            "exclusion": [
              "Interstitial lung disease of known etiology (e.g., domestic and occupational environmental exposures, connective tissue disease, drug toxicity, etc.).",
              "Other pulmonary diseases considered clinically significant by the investigator (e.g., asthma, chronic obstructive pulmonary disease, cavitary or pleural disease, etc.).",
              "Emphysema >= 50%, or emphysema greater than fibrosis, as determined by independent central imaging review of HRCT.",
              "Acute exacerbation of IPF within 3 months prior to screening or during the screening period, as judged by the investigator.",
              "Sustained improvement in IPF severity within 12 months prior to screening or during the screening period, as judged by the investigator based on changes in FVC, DLCO, and/or chest HRCT scan.",
              "Pre-bronchodilator forced expiratory volume in 1 second (FEV1)/FVC \\< 0.70 during the screening period.",
              "Known increase in FEV1 and/or FVC >= 12% and >= 200 mL post-bronchodilator.",
              "History of smoking within 3 months prior to screening or during the screening period, or inability to refrain from smoking (including cigarettes, cigars, pipes, and e-cigarettes) for the duration of the study.",
              "Completed a cardiopulmonary rehabilitation program focusing on exercise training within 8 weeks prior to screening, or planning to initiate such a program during the study.",
              "Presence of pulmonary hypertension or cor pulmonale that, in the investigator's opinion, would significantly limit compliance with study requirements or may affect assessment of study safety or efficacy."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation. * Aged >=40 years at the time of signing the ICF, with no gender restriction. * Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline. * HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available. * Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period. * Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period. * Meets either of the following: * The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study. * The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should disco"
          }
        },
        {
          "trial_id": "NCT04262167",
          "title": "Human Autologous Lung Stem Cell Transplant for Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT04262167",
          "retrieval_rank": 3,
          "retrieval_score": 337.309,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
          ],
          "phase": "PHASE1",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Lung Spheroid Stem Cells 100 million",
            "Lung Spheroid Stem Cells 200 million"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": 80,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04262167-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04262167-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": 80
              },
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Male or female between the ages of 40 to 80.",
              "Diagnosis of a Progressive Fibrotic Interstitial Lung Disease",
              "Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF:",
              "1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded.",
              "2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded.",
              "Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening).",
              "Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity.",
              "Ability to perform a 6-Minute Walk Test (6MWT) at screening.",
              "Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures"
            ],
            "exclusion": [
              "Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease.",
              "Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge.",
              "Evidence of sustained improvement lung function defined as improvement from pre-therapy pulmonary function tests (PFTs) observed with two or more successive post-therapy PFTs over the year prior to randomization.",
              "Active or recent (less than 60 days prior to enrollment) significant respiratory tract infections, or a history of frequent (greater than 2 per year for the last 2 years) infective exacerbations of IPF.",
              "Hospitalization within 60 days of screening for an acute exacerbation of IPF (AE-IPF).",
              "Chronic heart failure (NYHA class III/IV) or known left ventricular ejection fraction less than 45%.",
              "Acute or chronic impairment (other than dyspnea) which limits the ability to comply with study requirements and procedures including the 6MWT.",
              "Subject requires hemodialysis, peritoneal dialysis or hemofiltration.",
              "Infection with HIV",
              "Viral Hepatitis"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Male or female between the ages of 40 to 80. * Diagnosis of a Progressive Fibrotic Interstitial Lung Disease * Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF: 1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded. 2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded. * Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening). * Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity. * Ability to perform a 6-Minute Walk Test (6MWT) at screening. * Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures Exclusion Criteria: * Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease. * Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge. * Evidence of sustained improvement lung function defined as improvement from"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 4,
          "retrieval_score": 329.462,
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
          "retrieval_rank": 5,
          "retrieval_score": 296.251,
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
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00089",
      "patient_information_string": "Oncology referral note: SYN-GEN-00089 is a 53-year-old male with metastatic solid tumor. Stage is recorded as III. ECOG performance status is 1. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in CO. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00089",
        "age": 53,
        "sex": "male",
        "diagnosis": "metastatic solid tumor",
        "stage": "III",
        "ecog": 1,
        "location": {
          "country": "US",
          "state": "CO"
        },
        "scenario": "clear_candidate",
        "target_trial_id": "NCT07682337"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07682337",
          "title": "Study of Single and Multiple Oral Doses of SCB0020160 in Healthy Adult Male Subjects",
          "source_url": "https://clinicaltrials.gov/study/NCT07682337",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Solid Tumor",
            "Obesity",
            "Idiopathic Pulmonary Fibrosis"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "SCB0020160",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 65,
            "sex": "male",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07682337-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Solid Tumor",
                "Obesity",
                "Idiopathic Pulmonary Fibrosis"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07682337-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 65
              },
              "required": true
            },
            {
              "criterion_id": "NCT07682337-I-sex",
              "criterion_type": "inclusion",
              "criterion": "Patient recorded sex should match the trial sex criterion.",
              "structured_value": "male",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Healthy adult male volunteers in the opinion of the principal investigator or delegate, aged 18 to 65 years at screening",
              "Body weight more Than or equals to 45.0 kilograms per square meter at screening, with a body mass index (BMI) of more than or equals to18.0-kilogram Meter square and less than or equals to 32.0 Kilograms per meter square",
              "Body Mass Index (BMI, kilograms per square meter.) = Weight (kilogram)/\\[Height square meter\\]",
              "Eligible to participate in the study based on the results of physical examination, clinical laboratory tests, history taking, and other examinations performed at screening, as determined by the principal investigator or delegate",
              "Has voluntarily decided to participate and provided written or electronic consent to comply with the precautions after receiving a full explanation of the study and fully understanding it"
            ],
            "exclusion": [
              "Has a history of or currently has any disease, including clinically significant hepatobiliary (severe liver impairment, viral hepatitis, etc.), renal (severe renal impairment, etc.), neurological, immunological, respiratory, digestive, endocrine, hematologic and oncologic, cardiovascular (Torsades de pointes, etc.), urological, psychiatric (mood disorders, obsessive compulsive disorder, etc.), and sexual function disorders",
              "Has a history of or currently has a gastrointestinal disease (Crohn's disease, ulcerative colitis, etc.) that may affect the safety and pharmacokinetic evaluation of the investigational product, or has a history of gastrointestinal surgery (except for simple appendectomy or hernia surgery)",
              "Has a history of hypersensitivity to the active pharmaceutical ingredient and components of the investigational product, drugs in the same class as the active pharmaceutical ingredient, or other drugs (aspirin, antibiotics, etc.)",
              "Has genetic problems such as galactose intolerance, Lapp lactase deficiency, or glucose galactose malabsorption",
              "Has any of the following results in vital signs measured in a sitting position after resting for at least 5 minutes at screening",
              "Systolic blood pressure more than 80 millimeters of mercury or greater than or equal to140 mmHg",
              "Diastolic blood pressure less than 45 millimeters of mercury or greater than or equal to140 mmHg 90 millimeters of mercury",
              "Pulse rate less than 45 beats/min or \\> 105 beats/min",
              "Has any of the following results in the 12-lead electrocardiogram measured in a semi-supine position after resting for at least 5 minutes at screening, or has clinically significant rhythm findings",
              "QTcF less than 450 msec"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Healthy adult male volunteers in the opinion of the principal investigator or delegate, aged 18 to 65 years at screening * Body weight more Than or equals to 45.0 kilograms per square meter at screening, with a body mass index (BMI) of more than or equals to18.0-kilogram Meter square and less than or equals to 32.0 Kilograms per meter square * Body Mass Index (BMI, kilograms per square meter.) = Weight (kilogram)/\\[Height square meter\\] * Eligible to participate in the study based on the results of physical examination, clinical laboratory tests, history taking, and other examinations performed at screening, as determined by the principal investigator or delegate * Has voluntarily decided to participate and provided written or electronic consent to comply with the precautions after receiving a full explanation of the study and fully understanding it Exclusion Criteria: * Has a history of or currently has any disease, including clinically significant hepatobiliary (severe liver impairment, viral hepatitis, etc.), renal (severe renal impairment, etc.), neurological, immunological, respiratory, digestive, endocrine, hematologic and oncologic, cardiovascular (Torsades de pointes, etc.), urological, psychiatric (mood disorders, obsessive compulsive disorder, etc.), and sexual function disorders * Has a history of or currently has a gastrointestinal disease (Crohn's disease, ulcerative colitis, etc.) that may affect the safety and pharmacokinetic evaluation of the investigational product, or has a history of gastrointestinal surgery (except for simple appendectomy or hernia surgery) * Has a history of hypersensitivity to the active pharmaceutical ingredient and components of the investigational product, drugs in the same class as the active pharmaceutica"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 331.9,
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
          "retrieval_score": 256.907,
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
          "retrieval_score": 194.041,
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
          "trial_id": "NCT06861244",
          "title": "Embryonal Tumor With Multilayered Rosettes",
          "source_url": "https://clinicaltrials.gov/study/NCT06861244",
          "retrieval_rank": 5,
          "retrieval_score": 177.236,
          "conditions": [
            "Embryonal Tumor With Multilayered Rosettes",
            "Embryonal Tumor With Multilayered Rosettes, Nos"
          ],
          "phase": "PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "Radiotherapy (RT)",
            "Chemotherapy Drug, Cancer - Physician's Choice",
            "Non-Investigational Surgical Resection",
            "Temozolomide",
            "Tumor Tissue Sample",
            "Blood Sample",
            "Cerebrospinal Fluid (CSF) Sample"
          ],
          "known_structured_fields": {
            "min_age": null,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [
              "IV"
            ],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [
              "induction chemotherapy"
            ],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06861244-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Embryonal Tumor With Multilayered Rosettes",
                "Embryonal Tumor With Multilayered Rosettes, Nos"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06861244-I-stage",
              "criterion_type": "inclusion",
              "criterion": "Patient disease stage should be allowed.",
              "structured_value": [
                "IV"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06861244-I-prior-induction-chemotherapy",
              "criterion_type": "inclusion",
              "criterion": "Patient should have prior treatment: induction chemotherapy.",
              "structured_value": "induction chemotherapy",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "The eligibility criteria listed below are interpreted literally and cannot be waived.",
              "1. Participants must have either a molecularly or histologically confirmed embryonal tumor with multilayered rosettes.",
              "2. For enrollment, a confirmation of a minimum of 10-20 unstained formalin-fixed paraffin-embedded (FFPE) slides or 1 block (15-20 mg) with tumor content of 40% or greater is required. Anything less must be discussed and approved by the study chairs prior to enrollment.",
              "3. Prior Therapy:",
              "1. Cohort 1 participants must not have received any prior tumor-directed therapy other than surgical resection.",
              "2. Cohort 2 and 3 participants may receive tumor-directed therapy prior to enrollment. These participants must be discussed with study chairs prior to enrollment.",
              "4. Participants must not have received prior radiation for treatment of tumor.",
              "5. Participants of any age are eligible.",
              "6. Participants should begin induction chemotherapy within 28 days of the most recent definitive surgical procedure. Participants beginning therapy beyond 28 days from surgery, will need to discuss with study chairs.",
              "7. Cohort specific eligibility"
            ],
            "exclusion": [
              "1. Cohort 1 only: Participants who have received any prior tumor-directed therapy other than surgical intervention",
              "2. Participants who are receiving any other tumor directed investigational agents.",
              "3. History of allergic reactions attributed to compounds of similar chemical or biologic composition to the agents used in study.",
              "4. Uncontrolled intercurrent illness.",
              "5. Women of childbearing potential must not be pregnant or breast-feeding."
            ],
            "eligibility_criteria_excerpt": "The eligibility criteria listed below are interpreted literally and cannot be waived. Inclusion Criteria: 1. Participants must have either a molecularly or histologically confirmed embryonal tumor with multilayered rosettes. 2. For enrollment, a confirmation of a minimum of 10-20 unstained formalin-fixed paraffin-embedded (FFPE) slides or 1 block (15-20 mg) with tumor content of 40% or greater is required. Anything less must be discussed and approved by the study chairs prior to enrollment. 3. Prior Therapy: 1. Cohort 1 participants must not have received any prior tumor-directed therapy other than surgical resection. 2. Cohort 2 and 3 participants may receive tumor-directed therapy prior to enrollment. These participants must be discussed with study chairs prior to enrollment. 4. Participants must not have received prior radiation for treatment of tumor. 5. Participants of any age are eligible. 6. Participants should begin induction chemotherapy within 28 days of the most recent definitive surgical procedure. Participants beginning therapy beyond 28 days from surgery, will need to discuss with study chairs. 7. Cohort specific eligibility 1. Cohort 1: Gross-total resection, Eligible for early radiotherapy (please see age criteria below), and no evidence of metastatic disease. 2. Cohort 2: Gross-total resection, high dose chemotherapy (please see age criteria below), and no evidence of metastatic disease. 3. Cohort 3A: Metastatic or residual disease, and early radiotherapy. 4. Cohort 3B: Metastatic or residual disease, and high dose chemotherapy. 5. Radiotherapy Age Criteria (at the time of planned radiation): \\>12 months of age for participants with infratentorial tumor OR \\>15 months of age for participants with supratentorial tumor. For participants being treated on r"
          }
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00090",
      "patient_information_string": "Tumor board intake: SYN-GEN-00090 is a 71-year-old female with idiopathic pulmonary fibrosis (ipf). Stage is recorded as IV. ECOG performance status is 2. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No active interstitial lung disease is reported. No active autoimmune disease is reported. No uncontrolled cardiac disease is reported. The patient receives care in AZ. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00090",
        "age": 71,
        "sex": "female",
        "diagnosis": "idiopathic pulmonary fibrosis (ipf)",
        "stage": "IV",
        "ecog": 2,
        "flags": {
          "active_autoimmune_disease": false,
          "active_interstitial_lung_disease": false,
          "uncontrolled_cardiac_disease": false
        },
        "location": {
          "country": "US",
          "state": "AZ"
        },
        "scenario": "missing_biomarker",
        "target_trial_id": "NCT07447102"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07447102",
          "title": "Phase II Clinical Study of BC006 in Patients With Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT07447102",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis (IPF)"
          ],
          "phase": "PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "BC006",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": null,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "active_autoimmune_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07447102-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis (IPF)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07447102-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": null
              },
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-active-autoimmune-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active autoimmune disease.",
              "structured_value": "active_autoimmune_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07447102-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation.",
              "Aged >=40 years at the time of signing the ICF, with no gender restriction.",
              "Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline.",
              "HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available.",
              "Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period.",
              "Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period.",
              "Meets either of the following:",
              "The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study.",
              "The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should discontinue approved therapy to participate in this study. Treatment-nave patients must decline after full discussion with the investigator regarding the risks/benefits of such therapy.",
              "Patients of reproductive potential (male and female) must agree to use highly effective contraceptive methods (hormonal, barrier, or abstinence) from signing the ICF until at least 6 months after the last dose of study drug."
            ],
            "exclusion": [
              "Interstitial lung disease of known etiology (e.g., domestic and occupational environmental exposures, connective tissue disease, drug toxicity, etc.).",
              "Other pulmonary diseases considered clinically significant by the investigator (e.g., asthma, chronic obstructive pulmonary disease, cavitary or pleural disease, etc.).",
              "Emphysema >= 50%, or emphysema greater than fibrosis, as determined by independent central imaging review of HRCT.",
              "Acute exacerbation of IPF within 3 months prior to screening or during the screening period, as judged by the investigator.",
              "Sustained improvement in IPF severity within 12 months prior to screening or during the screening period, as judged by the investigator based on changes in FVC, DLCO, and/or chest HRCT scan.",
              "Pre-bronchodilator forced expiratory volume in 1 second (FEV1)/FVC \\< 0.70 during the screening period.",
              "Known increase in FEV1 and/or FVC >= 12% and >= 200 mL post-bronchodilator.",
              "History of smoking within 3 months prior to screening or during the screening period, or inability to refrain from smoking (including cigarettes, cigars, pipes, and e-cigarettes) for the duration of the study.",
              "Completed a cardiopulmonary rehabilitation program focusing on exercise training within 8 weeks prior to screening, or planning to initiate such a program during the study.",
              "Presence of pulmonary hypertension or cor pulmonale that, in the investigator's opinion, would significantly limit compliance with study requirements or may affect assessment of study safety or efficacy."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Must provide written informed consent form (ICF) indicating understanding of the study and voluntary participation. * Aged >=40 years at the time of signing the ICF, with no gender restriction. * Diagnosis of idiopathic pulmonary fibrosis (IPF) according to the 2022 American Thoracic Society/European Respiratory Society/Japanese Respiratory Society/Latin American Thoracic Society (ATS/ERS/JRS/ALAT) clinical practice guideline. * HRCT pattern consistent with usual interstitial pneumonia (UIP) or probable UIP for IPF confirmed by independent central imaging review (acceptable-quality HRCT obtained within 12 months prior to screening or during the screening period). If HRCT shows indeterminate UIP, the diagnosis of IPF must be confirmed by histopathology from a prior lung biopsy (surgical/video-assisted thoracoscopic lung biopsy or bronchoscopic cryobiopsy) recognized by the investigator, if available. * Forced vital capacity percent predicted (FVC% predicted) >=45% during the screening period. * Diffusing capacity of the lung for carbon monoxide percent predicted (DLCO% predicted), corrected for hemoglobin (Hb), >=30% and <=90% during the screening period. * Meets either of the following: * The patient has been on a stable dose of nintedanib or pirfenidone for at least 8 weeks prior to screening and during screening (nintedanib >=100 mg BID, pirfenidone >=400 mg TID, no dose changes), tolerates the treatment, and plans to continue this background therapy during the study. * The patient has not received nintedanib or pirfenidone for at least 4 weeks prior to screening and during screening (previous treatment discontinued or treatment-nave), and does not plan to initiate or re-initiate nintedanib or pirfenidone during the study. No patient should disco"
          }
        },
        {
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 2,
          "retrieval_score": 502.571,
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
          "retrieval_score": 450.579,
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
          "trial_id": "NCT04262167",
          "title": "Human Autologous Lung Stem Cell Transplant for Idiopathic Pulmonary Fibrosis",
          "source_url": "https://clinicaltrials.gov/study/NCT04262167",
          "retrieval_rank": 4,
          "retrieval_score": 399.702,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
          ],
          "phase": "PHASE1",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Lung Spheroid Stem Cells 100 million",
            "Lung Spheroid Stem Cells 200 million"
          ],
          "known_structured_fields": {
            "min_age": 40,
            "max_age": 80,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": [
              "active_interstitial_lung_disease",
              "uncontrolled_cardiac_disease"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT04262167-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis and Progressive Fibrotic Interstitial Lung Disease"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT04262167-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 40,
                "max_age": 80
              },
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT04262167-E-uncontrolled-cardiac-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has uncontrolled cardiac disease.",
              "structured_value": "uncontrolled_cardiac_disease",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Male or female between the ages of 40 to 80.",
              "Diagnosis of a Progressive Fibrotic Interstitial Lung Disease",
              "Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF:",
              "1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded.",
              "2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded.",
              "Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening).",
              "Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity.",
              "Ability to perform a 6-Minute Walk Test (6MWT) at screening.",
              "Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures"
            ],
            "exclusion": [
              "Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease.",
              "Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge.",
              "Evidence of sustained improvement lung function defined as improvement from pre-therapy pulmonary function tests (PFTs) observed with two or more successive post-therapy PFTs over the year prior to randomization.",
              "Active or recent (less than 60 days prior to enrollment) significant respiratory tract infections, or a history of frequent (greater than 2 per year for the last 2 years) infective exacerbations of IPF.",
              "Hospitalization within 60 days of screening for an acute exacerbation of IPF (AE-IPF).",
              "Chronic heart failure (NYHA class III/IV) or known left ventricular ejection fraction less than 45%.",
              "Acute or chronic impairment (other than dyspnea) which limits the ability to comply with study requirements and procedures including the 6MWT.",
              "Subject requires hemodialysis, peritoneal dialysis or hemofiltration.",
              "Infection with HIV",
              "Viral Hepatitis"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Male or female between the ages of 40 to 80. * Diagnosis of a Progressive Fibrotic Interstitial Lung Disease * Diagnosis of IPF based on the following criteria in accordance with American Thoracic Society (ATS) guidelines for diagnosing IPF: 1. Definite usual interstitial pneumonia (UIP) confirmed on surgical lung biopsy (SLB) with all other etiologies for UIP excluded OR High resolution CT scan (HRCT) showing definite UIP with all other etiologies for UIP excluded. 2. Probable UIP on both imaging and surgical lung biopsy with all other etiologies for UIP excluded. * Forced vital capacity (FVC) greater than 50% of predicted with a ratio of forced expiratory volume in 1 second to FVC (FEV1/FVC) greater than 0.75 (Pulmonary function tests must be completed no more than 90 days before screening). * Diffusing capacity for carbon monoxide (DLCO) greater than 25% of predicted capacity. * Ability to perform a 6-Minute Walk Test (6MWT) at screening. * Competency to understand the information given in the Human Research and Ethics Committee (HREC) approved Informed Consent Form and must sign the form prior to the initiation of any study procedures Exclusion Criteria: * Diagnosis of an interstitial lung disease (ILD) or restrictive lung disease other than IPF or Progressive Fibrotic Interstitial Lung Disease. * Obstructive lung disease as determined by evidence of airflow obstruction on HRCT or physiologic criteria including: FEV1/FVC ratio less than 0.75, Residual volume (RV) greater than 120% by plethysmography or significant (verified by radiologist) emphysema on HRCT or evidence of reactive airway disease by change in FEV1 of greater than 12% following bronchodilator challenge. * Evidence of sustained improvement lung function defined as improvement from"
          }
        },
        {
          "trial_id": "NCT07329959",
          "title": "CAR-DC for End-Stage IPF",
          "source_url": "https://clinicaltrials.gov/study/NCT07329959",
          "retrieval_rank": 5,
          "retrieval_score": 323.228,
          "conditions": [
            "Idiopathic Pulmonary Fibrosis(IPF)"
          ],
          "phase": "PHASE1",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "Leukapheresis",
            "CAR-DC"
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
              "active_interstitial_lung_disease",
              "active_uncontrolled_infection"
            ]
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07329959-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Idiopathic Pulmonary Fibrosis(IPF)"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07329959-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 75
              },
              "required": true
            },
            {
              "criterion_id": "NCT07329959-E-active-interstitial-lung-disease",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active interstitial lung disease.",
              "structured_value": "active_interstitial_lung_disease",
              "required": true
            },
            {
              "criterion_id": "NCT07329959-E-active-uncontrolled-infection",
              "criterion_type": "exclusion",
              "criterion": "Exclude if patient has active uncontrolled infection.",
              "structured_value": "active_uncontrolled_infection",
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "1\\. Aged between 18 and 75 years, inclusive, with a diagnosis of idiopathic pulmonary fibrosis (IPF).",
              "2\\. Ability to verbally confirm understanding of the risks, benefits, and alternative treatments associated with immunosuppressive CAR-DC therapy. Provision of written informed consent by the patient or their legally authorized representative prior to participation.",
              "3\\. Evidence of disease progression (worsening pulmonary fibrosis and declining lung function) despite treatment with standard therapies such as pirfenidone, nintedanib, or other appropriate regimens.",
              "4\\. Meets at least one criterion indicating eligibility for lung transplantation due to interstitial lung disease, while not consenting to a transplant. The criteria include:",
              "1. A decline in forced vital capacity (FVC) >=10% over a 6-month follow-up period.",
              "2. A decline in diffusing capacity of the lungs for carbon monoxide (DLCO) >=10% of predicted value over 6 months.",
              "3. Six-minute walk test results showing oxygen saturation \\<88%, a distance walked \\<250 meters, or a decline of \\>50 meters in distance over 6 months.",
              "4. Presence of pulmonary hypertension (PH) confirmed by right heart catheterization or transthoracic echocardiography.",
              "5. Hospitalization due to respiratory functional decline, pneumothorax, or acute exacerbation.",
              "5\\. No prior cellular immunotherapy within the last 3 months. 6. Hematological parameters meeting the following thresholds: hematocrit \\>30%, lymphocyte count \\>0.5 10/L, and platelet count \\>60 10/L."
            ],
            "exclusion": [
              "1. History of acute exacerbation of IPF within 4 weeks prior to screening or during the screening period.",
              "2. Presence of interstitial lung disease (ILD) other than IPF, including but not limited to: other forms of idiopathic interstitial pneumonia; ILD associated with fibrogenic agents, environmental exposures, or drug toxicity; other occupational lung diseases; granulomatous lung diseases; pulmonary vascular diseases; or ILD related to systemic diseases (e.g., vasculitis, infections such as tuberculosis, connective tissue diseases). Cases with uncertain diagnosis require serological testing and/or multidisciplinary team review for confirmation.",
              "3. Presence of significant active infection.",
              "4. History of malignancy, except for malignancies treated with curative intent and with no recurrence for >=5 years, resected basal cell or squamous cell skin carcinoma, carcinoma in situ of the cervix, or resected colonic polyps.",
              "5. Significant history of infectious diseases.",
              "6. Presence of psychiatric illness or other conditions that would compromise the patient's ability to cooperate with study requirements, comply with treatment, or undergo monitoring.",
              "7. Known hypersensitivity to any component of the immunosuppressive CAR-DC cell product.",
              "8. History of severe renal failure requiring renal dialysis, or serum creatinine level \\>2.5 mg/dL.",
              "9. Any contraindication to the investigational product or study procedures.",
              "10. Pregnancy or lactation."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: 1\\. Aged between 18 and 75 years, inclusive, with a diagnosis of idiopathic pulmonary fibrosis (IPF). 2\\. Ability to verbally confirm understanding of the risks, benefits, and alternative treatments associated with immunosuppressive CAR-DC therapy. Provision of written informed consent by the patient or their legally authorized representative prior to participation. 3\\. Evidence of disease progression (worsening pulmonary fibrosis and declining lung function) despite treatment with standard therapies such as pirfenidone, nintedanib, or other appropriate regimens. 4\\. Meets at least one criterion indicating eligibility for lung transplantation due to interstitial lung disease, while not consenting to a transplant. The criteria include: 1. A decline in forced vital capacity (FVC) >=10% over a 6-month follow-up period. 2. A decline in diffusing capacity of the lungs for carbon monoxide (DLCO) >=10% of predicted value over 6 months. 3. Six-minute walk test results showing oxygen saturation \\<88%, a distance walked \\<250 meters, or a decline of \\>50 meters in distance over 6 months. 4. Presence of pulmonary hypertension (PH) confirmed by right heart catheterization or transthoracic echocardiography. 5. Hospitalization due to respiratory functional decline, pneumothorax, or acute exacerbation. 5\\. No prior cellular immunotherapy within the last 3 months. 6. Hematological parameters meeting the following thresholds: hematocrit \\>30%, lymphocyte count \\>0.5 10/L, and platelet count \\>60 10/L. Exclusion Criteria: 1. History of acute exacerbation of IPF within 4 weeks prior to screening or during the screening period. 2. Presence of interstitial lung disease (ILD) other than IPF, including but not limited to: other forms of idiopathic interstitial pneumonia; I"
          }
        }
      ]
    }
  ]
}
