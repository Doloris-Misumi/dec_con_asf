# v1.0 full-set Sedan conf=0.3 deduplicated leaderboard

- Source ledger: `/home/hongsheng/dec_con_asf/analysis_exports/v1_all_results_big_table_260817.csv`
- Rows after de-duplication by project/method/experiment/conf: 38
- Includes full `all` rows from `full`, `full_conditional`, and `full_or_exported_summary` scopes.
- Sorted by 3D AP@0.3, then BEV AP@0.3, then mean of available AP columns.
- `paper_or_compiled_json` rows are reference/compiled rows, not necessarily fresh measured runs.

| rank | project | method | experiment | kind | scope | epoch | BEV@0.7 | 3D@0.7 | BEV@0.5 | 3D@0.5 | BEV@0.3 | 3D@0.3 | mean |
|---:|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | dec_con_asf | TaskDec MoreOpenGate | exp_260817_000507_TaskDecControlMoreOpenGate_v1_0... | complete_results | full_conditional | 2 | 62.22510585911386 | 22.067578029928576 | 80.35314420068977 | 67.79206685242468 | 88.99886089260256 | 88.51152651560379 | 68.32471372506053 |
| 2 | dec_con_asf | TaskDec Robust | exp_260813_203247_TaskDecControlRobust_v1_0_A2FUS... | full_eval_summary | full_or_exported_summary | - | 62.63 | 22.03 | 88.09 | 67.5 | 88.84 | 88.36 | 69.575 |
| 3 | dec_con_asf | TaskDec Robust | exp_260812_232650_TaskDecControlRobust_v1_0_A2FUS... | complete_results | full_conditional | 0 | 62.63218901253204 | 22.03903704773203 | 88.09529078343822 | 67.50133716157292 | 88.83900978912645 | 88.3550327583966 | 69.5769827587997 |
| 4 | dec_con_asf | Robust best-subset model0 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 62.63218901253204 | 22.03903704773203 | 88.09529078343822 | 67.50133716157292 | 88.83900978912645 | 88.3550327583966 | 69.5769827587997 |
| 5 | dec_con_asf | TaskDec MoreOpenGate | exp_260817_000340_TaskDecControlMoreOpenGate_v1_0... | complete_results | full_conditional | 0 | 62.30087515913397 | 21.313762672157626 | 87.77254251995508 | 67.20184259803186 | 88.61964661569957 | 88.08776029892891 | 69.2160716439845 |
| 6 | dec_con_asf | TaskDec Balanced | exp_260810_221300_TaskDecControlBalanced_v1_0_A2F... | complete_results | full | - | 63.39200313499607 | 19.647517350211327 | 80.48399601452854 | 67.44712259119997 | 80.92657798314836 | 80.59120185885928 | 65.41473648882392 |
| 7 | dec_con_asf | Balanced final model10 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 63.39200313499607 | 19.647517350211327 | 80.48399601452854 | 67.44712259119997 | 80.92657798314836 | 80.59120185885928 | 65.41473648882392 |
| 8 | dec_con_asf | TaskDec Balanced v1 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 63.39200313499607 | 19.647517350211327 | 80.48399601452854 | 67.44712259119997 | 80.92657798314836 | 80.59120185885928 | 65.41473648882392 |
| 9 | dec_con_asf | TaskDec MoreOpenGate | exp_260813_225556_TaskDecControlMoreOpenGate_v1_0... | complete_results | full | - | 61.759395530750346 | 19.376958915948308 | 80.45452214867144 | 67.76645618703083 | 89.10255710851837 | 80.5831446401509 | 66.50717242184503 |
| 10 | dec_con_asf | TaskDec StrongerControl | exp_260813_225557_TaskDecControlStrongerControl_v... | complete_results | full | - | 62.97452315099276 | 22.778343663414 | 80.45699101321094 | 67.85519694521007 | 89.00067025674609 | 80.52223604195824 | 67.26466017858868 |
| 11 | dec_con_asf | TaskDec StrongerControl | exp_260817_000340_TaskDecControlStrongerControl_v... | complete_results | full_conditional | 4 | 63.080564342436396 | 18.992489743449113 | 80.51957514189391 | 67.69610335715845 | 88.99093964676943 | 80.51613712851278 | 66.63263489337001 |
| 12 | dec_con_asf | TaskDec StrongerControl | exp_260817_000503_TaskDecControlStrongerControl_v... | complete_results | full_conditional | 2 | 62.479048522976555 | 22.43438933448783 | 80.41872349373944 | 68.06391709415315 | 89.0589940614117 | 80.5081254152946 | 67.16053298701054 |
| 13 | K-Radar-main | ASF v1 official/local | exp_260814_212832_ASF_v1_0_local_repro | complete_results | full | - | 63.10708440787629 | 22.95129787234395 | 80.4457359516899 | 67.71598904935695 | 89.14500596681748 | 80.44650465152583 | 67.30193631660173 |
| 14 | dec_con_asf | TaskDec Robust | exp_260810_221258_TaskDecControlRobust_v1_0_A2FUS... | complete_results | full | - | 62.33962398170383 | 22.315618443567757 | 80.42524501100696 | 67.20669584968023 | 80.87225044046366 | 80.42498136197386 | 65.59740251473272 |
| 15 | dec_con_asf | Robust final model10 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 62.33962398170383 | 22.315618443567757 | 80.42524501100696 | 67.20669584968023 | 80.87225044046366 | 80.42498136197386 | 65.59740251473272 |
| 16 | dec_con_asf | TaskDec Robust v1 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 62.33962398170383 | 22.315618443567757 | 80.42524501100696 | 67.20669584968023 | 80.87225044046366 | 80.42498136197386 | 65.59740251473272 |
| 17 | dec_con_asf | TaskDec Balanced | exp_260812_232646_TaskDecControlBalanced_v1_0_A2F... | complete_results | full_conditional | 2 | 62.69029290276765 | 21.897254577063126 | 80.37988453218126 | 67.57076206277459 | 89.01024720092134 | 80.37174196903251 | 66.98669720745674 |
| 18 | dec_con_asf | Balanced best-subset model2 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 62.69029290276765 | 21.897254577063126 | 80.37988453218126 | 67.57076206277459 | 89.01024720092134 | 80.37174196903251 | 66.98669720745674 |
| 19 | K-Radar-main | ASF v1 official/local | exp_250303_200024_A2F_v1_0 | complete_results | full | - | 62.85129838117256 | 18.84758961438235 | 80.32516486241366 | 67.19240527543302 | 80.77711184770162 | 80.31346659416178 | 65.05117276254417 |
| 20 | dec_con_asf | Official ASF v1 conf0.3 | dec_con_asf | paper_or_compiled_json |  | - | 62.85129838117256 | 18.84758961438235 | 80.32516486241366 | 67.19240527543302 | 80.77711184770162 | 80.31346659416178 | 65.05117276254417 |
| 21 | K-Radar-main | ASF v2 official | exp_250218_134456_A2FUSION_rlc_l1d256_l2p2t32d256... | summary_conf_md | full_or_exported_summary | - | 43.21 | 11.85 | 71.7 | 52.09 | 77.85 | 74.98 | 55.28 |
| 22 | K-Radar-main | ASF/A2Fusion | exp_260725_230526_A2FUSION_rlc_l1d256_l2p2t32d256... | complete_results | full | - | 42.788269153965786 | 11.80060982640327 | 71.31973045770901 | 51.76322972108183 | 77.44271519762323 | 74.61048177743548 | 54.95417268903643 |
| 23 | asf_patch_dec | ObjPatchDec Strong | exp_260803_210429_ObjPatchDecStrong_A2FUSION_rlc_... | full_eval_summary | full_or_exported_summary | - | 42.74 | 11.21 | 71.13 | 51.67 | 77.33 | 74.54 | 54.77 |
| 24 | asf_patch_dec | ObjPatchDec Strong | exp_260803_210429_ObjPatchDecStrong_model8_full | full_eval_summary | full_or_exported_summary | - | 42.74 | 11.21 | 71.13 | 51.67 | 77.33 | 74.54 | 54.77 |
| 25 | asf_patch_dec | PatchDec | exp_260726_144405_PatchDec_A2FUSION_rlc_l1d256_l2... | summary_conf_md | full_or_exported_summary | - | 42.25 | 11.62 | 71.22 | 51.5 | 75.18 | 74.48 | 54.375 |
| 26 | asf_patch_dec | ObjPatchDec Strong | exp_260728_181732_ObjPatchDecStrong_A2FUSION_rlc_... | summary_conf_md | full_or_exported_summary | - | 43.15 | 12.51 | 71.09 | 51.89 | 75.17 | 74.48 | 54.715 |
| 27 | asf_patch_dec | PatchDec | exp_260728_162524_PatchDec_A2FUSION_rlc_l1d256_l2... | summary_conf_md | full_or_exported_summary | - | 42.42 | 11.01 | 71.09 | 51.16 | 77.33 | 74.46 | 54.578333333333326 |
| 28 | asf_patch_dec | DecControlledASF Gentle | exp_260728_181732_ObjPatchDecGentle_A2FUSION_rlc_... | summary_conf_md | full_or_exported_summary | - | 42.74 | 12.07 | 69.26 | 51.86 | 75.27 | 72.54 | 53.95666666666667 |
| 29 | K-Radar-main | ASF/A2Fusion | exp_260721_133144_ASF_LR_bs4_ep15 | summary_conf_md | full_or_exported_summary | - | 38.04 | 9.65 | 66.13 | 46.05 | 72.48 | 69.37 | 50.28666666666667 |
| 30 | K-Radar-main | DeCU-ASF | exp_260721_133144_DeCU_ASF_LR_bs4_ep15 | summary_conf_md | full_or_exported_summary | - | 37.78 | 9.82 | 66.11 | 45.88 | 72.47 | 69.28 | 50.223333333333336 |
| 31 | decu_asf | DeCU-ASF | exp_260721_133144_DeCU_ASF_LR_bs4_ep15 | summary_conf_md | full_or_exported_summary | - | 37.78 | 9.82 | 66.11 | 45.88 | 72.47 | 69.28 | 50.223333333333336 |
| 32 | K-Radar-main | SECOND | exp_260715_125207_SECOND | summary_conf_md | full_or_exported_summary | - | 44.13 | 16.25 | 68.34 | 45.25 | 70.08 | 68.28 | 52.055 |
| 33 | decu_asf | DeCU-ASF | exp_260725_230532_DeCU_A2FUSION_rlc_l1d256_l2p2t3... | complete_results | full | - | 19.74857469936415 | 2.4284917424335735 | 60.625755032841376 | 36.88682443866289 | 68.63176750940538 | 67.70555245374726 | 42.67116097940911 |
| 34 | K-Radar-main | ASF/A2Fusion | exp_260717_184456_A2FUSION_rlc_l1d256_l2p2t32d256... | summary_conf_md | full_or_exported_summary | - | 37.36 | 9.85 | 63.92 | 44.47 | 70.23 | 67.1 | 48.821666666666665 |
| 35 | K-Radar-main | ASF/A2Fusion | exp_260721_133145_ASF_LR_bs8_ep30 | summary_conf_md | full_or_exported_summary | - | 31.68 | 5.89 | 62.44 | 40.33 | 69.94 | 66.68 | 46.16 |
| 36 | decu_asf | DeCU-ASF | exp_260721_133144_DeCU_ASF_LR_bs8_ep30 | summary_conf_md | full_or_exported_summary | - | 37.57 | 8.23 | 61.82 | 44.15 | 67.97 | 64.92 | 47.443333333333335 |
| 37 | v2 | RL_3df_gate / DeCU-ASF early | exp_260714_024354_RL_3df_gate | summary_conf_md | full_or_exported_summary | - | 11.39 | 0.65 | 49.87 | 15.03 | 69.73 | 57.0 | 33.945 |
| 38 | K-Radar-main | RTNH | exp_260717_130203_RTNH | summary_conf_md | full_or_exported_summary | - | 17.17 | 4.62 | 40.9 | 22.85 | 52.75 | 46.56 | 30.808333333333334 |
