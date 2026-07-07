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
  "batch_id": "gpt_e2e_teacher_batch_12",
  "patients": [
    {
      "patient_id": "SYN-GEN-00056",
      "patient_information_string": "Tumor board intake: SYN-GEN-00056 is a 54-year-old female with migraine. Stage is recorded as III. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in IL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00056",
        "age": 54,
        "sex": "female",
        "diagnosis": "migraine",
        "stage": "III",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "IL"
        },
        "scenario": "prior_treatment_gap",
        "target_trial_id": "NCT06695156"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT06695156",
          "title": "Exploring the Effect of the Transcendental Meditation Technique on Migraine Frequency and Functionality: A Single Arm Study",
          "source_url": "https://clinicaltrials.gov/study/NCT06695156",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Migraine",
            "Migraine With or Without Aura"
          ],
          "phase": "NA",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Meditation"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 60,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06695156-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Migraine",
                "Migraine With or Without Aura"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06695156-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 60
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Diagnosis of migraine with or without aura, based on ICHD3 criteria",
              "6-14 migraine days/month.",
              ">= one-year history of migraines starting before the age of 50.",
              ">= 18 years old or <= 60 Years old",
              "Willing to attend follow-up sessions.",
              "Willing to practice TM twice a day for 20 minutes.",
              "Fluent in English.",
              "Willing to continue the same medication without any additional medicine",
              "In good general health, with no other diseases expected to interfere with the study."
            ],
            "exclusion": [
              "\\> 60 years old or \\< 18 Years old",
              "Already practicing Transcendental Meditation.",
              "Pre-diagnosed major systemic illness or unstable medical/psychiatric condition (eg, suicide risk) requiring immediate treatment or that could compromise protocol adherence",
              "Medication overuse headache (MOH)",
              "Current/planned pregnancy or breastfeeding",
              "New prophylactic migraine medicine started within 4 weeks of the screening visit",
              "Unwilling to maintain stable migraine medication dosages",
              "Failure to complete baseline headache logs."
            ],
            "eligibility_criteria_excerpt": "Inclusion criteria: * Diagnosis of migraine with or without aura, based on ICHD3 criteria * 6-14 migraine days/month. * >= one-year history of migraines starting before the age of 50. * >= 18 years old or <= 60 Years old * Willing to attend follow-up sessions. * Willing to practice TM twice a day for 20 minutes. * Fluent in English. Willing to continue the same medication without any additional medicine In good general health, with no other diseases expected to interfere with the study. Exclusion criteria: * \\> 60 years old or \\< 18 Years old * Already practicing Transcendental Meditation. * Pre-diagnosed major systemic illness or unstable medical/psychiatric condition (eg, suicide risk) requiring immediate treatment or that could compromise protocol adherence * Medication overuse headache (MOH) * Current/planned pregnancy or breastfeeding * New prophylactic migraine medicine started within 4 weeks of the screening visit * Unwilling to maintain stable migraine medication dosages * Failure to complete baseline headache logs."
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 268.564,
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
          "retrieval_score": 198.791,
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
        },
        {
          "trial_id": "NCT06830031",
          "title": "Clinical Study of C402-CD19-CAR Treatment in Subjects With Relapsed or Refractory B-cell Lymphoma",
          "source_url": "https://clinicaltrials.gov/study/NCT06830031",
          "retrieval_rank": 5,
          "retrieval_score": 164.256,
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
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00057",
      "patient_information_string": "Oncology referral note: SYN-GEN-00057 is a 9-year-old female with migraine. Stage is recorded as IV. ECOG performance status is 2. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in FL. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00057",
        "age": 9,
        "sex": "female",
        "diagnosis": "migraine",
        "stage": "IV",
        "ecog": 2,
        "location": {
          "country": "US",
          "state": "FL"
        },
        "scenario": "clear_candidate",
        "target_trial_id": "NCT05127954"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT05127954",
          "title": "Long-term Extension Study to Assess Safety and Tolerability of Oral Ubrogepant Tablets for the Acute Treatment of Migraine in Pediatric Participants (Ages 6-17)",
          "source_url": "https://clinicaltrials.gov/study/NCT05127954",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Migraine"
          ],
          "phase": "PHASE3",
          "status": "ENROLLING_BY_INVITATION",
          "interventions": [
            "Ubrogepant"
          ],
          "known_structured_fields": {
            "min_age": 6,
            "max_age": 17,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT05127954-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Migraine"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT05127954-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 6,
                "max_age": 17
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Completers of the lead-in Study 3110-305-002 (in the main study or PK cohort) or those who screen failed due to being placebo responders.",
              "Demonstrated an acceptable degree of compliance with study procedures in the lead-in study and who, in the investigator's clinical judgment, did not experience an AE that may indicate an unacceptable safety risk for this study."
            ],
            "exclusion": [
              "Requirement for any medication (eg, barbiturates) or diet (eg, grapefruit juice) that is on the list of prohibited concomitant medications that cannot be discontinued or switched to an allowable, alternative medication at Visit 1.",
              "An ECG with clinically significant abnormalities at Visit 1 as determined by the investigator.",
              "Clinically significant abnormalities in physical examination at Visit 1, as determined by the investigator.",
              "Significant risk of self-harm, based on clinical interview and responses on the C-SSRS, or of harm to others in the opinion of the investigator; participants should be excluded if they report suicidal ideation with intent, with or without a plan (ie, Type 4 or 5 on the C-SSRS), or report suicidal behavior at Visit 1",
              "Any medical or other reason (eg, unlikely to adhere to the study procedures, keep appointments, or is planning to relocate during the study) that, in the investigator's opinion, might indicate that the participant is unsuitable for the study."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Completers of the lead-in Study 3110-305-002 (in the main study or PK cohort) or those who screen failed due to being placebo responders. * Demonstrated an acceptable degree of compliance with study procedures in the lead-in study and who, in the investigator's clinical judgment, did not experience an AE that may indicate an unacceptable safety risk for this study. Exclusion Criteria: * Requirement for any medication (eg, barbiturates) or diet (eg, grapefruit juice) that is on the list of prohibited concomitant medications that cannot be discontinued or switched to an allowable, alternative medication at Visit 1. * An ECG with clinically significant abnormalities at Visit 1 as determined by the investigator. * Clinically significant abnormalities in physical examination at Visit 1, as determined by the investigator. * Significant risk of self-harm, based on clinical interview and responses on the C-SSRS, or of harm to others in the opinion of the investigator; participants should be excluded if they report suicidal ideation with intent, with or without a plan (ie, Type 4 or 5 on the C-SSRS), or report suicidal behavior at Visit 1 * Any medical or other reason (eg, unlikely to adhere to the study procedures, keep appointments, or is planning to relocate during the study) that, in the investigator's opinion, might indicate that the participant is unsuitable for the study."
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 240.786,
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
          "trial_id": "NCT07091617",
          "title": "Testing an Enhanced Digital Delivery Model for Inherited Cancer Genetic Testing in Young Adults With Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT07091617",
          "retrieval_rank": 3,
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
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 4,
          "retrieval_score": 179.146,
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
          "retrieval_rank": 5,
          "retrieval_score": 137.8,
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
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00058",
      "patient_information_string": "Tumor board intake: SYN-GEN-00058 is a 63-year-old female with migraine with aura. Stage is recorded as III. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in PA. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00058",
        "age": 63,
        "sex": "female",
        "diagnosis": "migraine with aura",
        "stage": "III",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "PA"
        },
        "scenario": "missing_biomarker",
        "target_trial_id": "NCT07342296"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07342296",
          "title": "Induction of Migraine Attacks With Aura Using Pituitary Adenylate Cyclase Activating Polypeptide-38",
          "source_url": "https://clinicaltrials.gov/study/NCT07342296",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Migraine With Aura",
            "Migraine Aura"
          ],
          "phase": "NA",
          "status": "NOT_YET_RECRUITING",
          "interventions": [
            "Pituitary Adenylate Cyclase Activating Polypeptide-38 (PACAP-38)",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 65,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07342296-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Migraine With Aura",
                "Migraine Aura"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07342296-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 65
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Age 18 to 65 years of age upon entry into screening",
              "History of migraine with aura for >= 12 months according to the International Classification of Headache Disorders 3rd Edition (ICHD-3) criteria",
              ">= 1 monthly day with aura that meets criteria as aura on average across the three months before screening",
              "Provision of informed consent prior to initiation of any study-specific activities/procedures."
            ],
            "exclusion": [
              "Any history of a primary or secondary headache disorder other than migraine without aura, migraine with aura, chronic migraine, and episodic tension-type headache",
              "History or evidence of any other clinically significant disorder, condition, or disease (except for those outlined above) that, in the opinion of the site investigator, would pose a risk to subject safety or interfere with study evaluation, procedures or completion",
              "The subject is at risk of self-harm or harm to others as evidenced by past suicidal behavior",
              "Female subjects of childbearing potential with a positive pregnancy test during any study visit",
              "Cardiovascular disease of any kind, including cerebrovascular diseases Hypertension (systolic blood pressure of >=150 mmHg and/or diastolic blood pressure of >=100 mmHg) prior to the start of infusion on the experimental day Hypotension (systolic blood pressure of <=90 mmHg and/or diastolic blood pressure of <=50 mmHg)",
              "Initiation, discontinuation, or change of dosing of prophylactic medications within 2 months prior to study inclusion",
              "Intake of acute medications (e.g. analgesics, triptans) within 48 hours of infusion start",
              "Headache of any intensity within 48 hours of infusion start",
              "Aura within 48 hours of infusion start"
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Age 18 to 65 years of age upon entry into screening * History of migraine with aura for >= 12 months according to the International Classification of Headache Disorders 3rd Edition (ICHD-3) criteria * >= 1 monthly day with aura that meets criteria as aura on average across the three months before screening * Provision of informed consent prior to initiation of any study-specific activities/procedures. Exclusion Criteria: * Any history of a primary or secondary headache disorder other than migraine without aura, migraine with aura, chronic migraine, and episodic tension-type headache * History or evidence of any other clinically significant disorder, condition, or disease (except for those outlined above) that, in the opinion of the site investigator, would pose a risk to subject safety or interfere with study evaluation, procedures or completion * The subject is at risk of self-harm or harm to others as evidenced by past suicidal behavior * Female subjects of childbearing potential with a positive pregnancy test during any study visit * Cardiovascular disease of any kind, including cerebrovascular diseases Hypertension (systolic blood pressure of >=150 mmHg and/or diastolic blood pressure of >=100 mmHg) prior to the start of infusion on the experimental day Hypotension (systolic blood pressure of <=90 mmHg and/or diastolic blood pressure of <=50 mmHg) * Initiation, discontinuation, or change of dosing of prophylactic medications within 2 months prior to study inclusion * Intake of acute medications (e.g. analgesics, triptans) within 48 hours of infusion start * Headache of any intensity within 48 hours of infusion start * Aura within 48 hours of infusion start"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 258.021,
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
          "retrieval_score": 198.791,
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
        },
        {
          "trial_id": "NCT06830031",
          "title": "Clinical Study of C402-CD19-CAR Treatment in Subjects With Relapsed or Refractory B-cell Lymphoma",
          "source_url": "https://clinicaltrials.gov/study/NCT06830031",
          "retrieval_rank": 5,
          "retrieval_score": 164.256,
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
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00059",
      "patient_information_string": "Oncology referral note: SYN-GEN-00059 is a 26-year-old male with tinnitus. Stage is recorded as III. ECOG performance status is 2. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in CO. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00059",
        "age": 26,
        "sex": "male",
        "diagnosis": "tinnitus",
        "stage": "III",
        "ecog": 2,
        "location": {
          "country": "US",
          "state": "CO"
        },
        "scenario": "exclusion_conflict",
        "target_trial_id": "NCT06799169"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT06799169",
          "title": "Management of Acute Tinnitus With Migraine Medications",
          "source_url": "https://clinicaltrials.gov/study/NCT06799169",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Tinnitus"
          ],
          "phase": "PHASE4",
          "status": "ACTIVE_NOT_RECRUITING",
          "interventions": [
            "Nortriptyline",
            "Topiramate",
            "Paroxetine",
            "Verapamil"
          ],
          "known_structured_fields": {
            "min_age": 25,
            "max_age": 85,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT06799169-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Tinnitus"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT06799169-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 25,
                "max_age": 85
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Patients with mild to moderate tinnitus.",
              "Male or female between the ages of 25 to 85 years.",
              "Subjects must be compliant with the medication and attend study visits.",
              "Must be able to read and write in the English language to provide consent."
            ],
            "exclusion": [
              "Pregnancy will result in automatic exclusion from the study. Rule out of pregnancy will be done by urine pregnancy test to confirm the situation for all women who are of childbearing potential.",
              "Subjects with a history of an adverse reaction to medication being prescribed.",
              "Subjects suffering from a medical condition or have a history that may be concerning to the investigator's clinical opinion."
            ],
            "eligibility_criteria_excerpt": "Inclusion Criteria: * Patients with mild to moderate tinnitus. * Male or female between the ages of 25 to 85 years. * Subjects must be compliant with the medication and attend study visits. * Must be able to read and write in the English language to provide consent. Exclusion Criteria: * Pregnancy will result in automatic exclusion from the study. Rule out of pregnancy will be done by urine pregnancy test to confirm the situation for all women who are of childbearing potential. * Subjects with a history of an adverse reaction to medication being prescribed. * Subjects suffering from a medical condition or have a history that may be concerning to the investigator's clinical opinion. * All contraindications for the medications that prevent subjects from randomization will be considered as exclusion criteria."
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 239.249,
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
          "trial_id": "NCT07091617",
          "title": "Testing an Enhanced Digital Delivery Model for Inherited Cancer Genetic Testing in Young Adults With Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT07091617",
          "retrieval_rank": 3,
          "retrieval_score": 186.676,
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
          "trial_id": "NCT04724018",
          "title": "Sacituzumab Govitecan Plus EV in Metastatic UC",
          "source_url": "https://clinicaltrials.gov/study/NCT04724018",
          "retrieval_rank": 4,
          "retrieval_score": 183.635,
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
          "retrieval_rank": 5,
          "retrieval_score": 139.686,
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
        }
      ]
    },
    {
      "patient_id": "SYN-GEN-00060",
      "patient_information_string": "Tumor board intake: SYN-GEN-00060 is a 46-year-old female with migraine. Stage is recorded as I. ECOG performance status is 0. Molecular testing results are not available in the note. No prior systemic therapy is listed in the referral. No explicit exclusion comorbidities are addressed. The patient receives care in AZ. The note is a synthetic record created for software testing, not a real patient chart.",
      "synthetic_source_profile": {
        "patient_id": "SYN-GEN-00060",
        "age": 46,
        "sex": "female",
        "diagnosis": "migraine",
        "stage": "I",
        "ecog": 0,
        "location": {
          "country": "US",
          "state": "AZ"
        },
        "scenario": "stage_conflict",
        "target_trial_id": "NCT07616128"
      },
      "candidate_trials": [
        {
          "trial_id": "NCT07616128",
          "title": "Study of EVO756 in Adults With Migraine",
          "source_url": "https://clinicaltrials.gov/study/NCT07616128",
          "retrieval_rank": 1,
          "retrieval_score": 1.0,
          "conditions": [
            "Migraine"
          ],
          "phase": "PHASE2",
          "status": "RECRUITING",
          "interventions": [
            "EVO756, Dose 1",
            "EVO756, Dose 2",
            "Placebo"
          ],
          "known_structured_fields": {
            "min_age": 18,
            "max_age": 64,
            "sex": "all",
            "allowed_stages": [],
            "max_ecog": null,
            "required_biomarkers": {},
            "required_prior_treatments": [],
            "excluded_flags": []
          },
          "criteria_to_assess": [
            {
              "criterion_id": "NCT07616128-I-condition",
              "criterion_type": "inclusion",
              "criterion": "Patient diagnosis should match the trial condition.",
              "structured_value": [
                "Migraine"
              ],
              "required": true
            },
            {
              "criterion_id": "NCT07616128-I-age",
              "criterion_type": "inclusion",
              "criterion": "Patient age should be within trial bounds.",
              "structured_value": {
                "min_age": 18,
                "max_age": 64
              },
              "required": true
            }
          ],
          "raw_criteria_excerpt": {
            "inclusion": [
              "Adults aged 18 to \\<65 years",
              "Migraine with or without aura, per ICHD-3 criteria",
              "History of failure with prior preventive migraine treatments",
              "Not currently using migraine preventive therapy"
            ],
            "exclusion": [
              "Difficulty distinguishing migraine from other headache types or presence of other primary headache disorders",
              "Use of certain medications",
              "Any clinically significant medical, psychiatric, neurological, cardiovascular, or laboratory abnormalities"
            ],
            "eligibility_criteria_excerpt": "Key Inclusion Criteria: * Adults aged 18 to \\<65 years * Migraine with or without aura, per ICHD-3 criteria * History of failure with prior preventive migraine treatments * Not currently using migraine preventive therapy Key Exclusion Criteria: * Difficulty distinguishing migraine from other headache types or presence of other primary headache disorders * Use of certain medications * Any clinically significant medical, psychiatric, neurological, cardiovascular, or laboratory abnormalities"
          }
        },
        {
          "trial_id": "NCT03237780",
          "title": "Atezolizumab With or Without Eribulin Mesylate in Treating Patients With Recurrent Locally Advanced or Metastatic Urothelial Cancer",
          "source_url": "https://clinicaltrials.gov/study/NCT03237780",
          "retrieval_rank": 2,
          "retrieval_score": 240.497,
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
          "retrieval_score": 188.276,
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
          "retrieval_score": 167.229,
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
          "trial_id": "NCT06830031",
          "title": "Clinical Study of C402-CD19-CAR Treatment in Subjects With Relapsed or Refractory B-cell Lymphoma",
          "source_url": "https://clinicaltrials.gov/study/NCT06830031",
          "retrieval_rank": 5,
          "retrieval_score": 157.246,
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
        }
      ]
    }
  ]
}
