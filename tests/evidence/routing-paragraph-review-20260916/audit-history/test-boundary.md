# Markdown 写作语义与 Python 维护测试边界审计

审计日期：2026-09-16。范围：本 worktree 的 17 个 `tests/test_*.py`、4 个 Python 工具及发布 policy；只读分析，未修改产品、测试、历史证据或 CI。此报告本身写在本地 `.release/`。

## 结论

应卸下直接审判 SKILL/reference 措辞、加载语义、固定字数和旧成稿写法的 Python 断言；保留三个运行扫描器、打包器、脱敏器以及仍保留 Python 工具的真实行为测试。不能按文件名含 `semantic`、`language` 或 `prompt` 就整文件删除。尤其 `test_final_body_lint.py` 是 Python finding 行为测试，应完整保留。

本审计将“函数输入→函数输出”与“某稿件是否写得对”分开。前者即使涉及词频或旧评测格式，也是现存 Python 的维护范围；后者包括读取 SKILL/旧正文后 assertIn/NotIn 某句话，属于应卸下的写作语义门。保留旧工具的单元测试，不等于保留旧工具作为新候选的写作准入门。

最明显的反向诱导：`test_v003_citation_sanity.py:87–98` 把“未读取”“不能支持”“不能|无法”写成旧稿必含词；`test_long_form_evidence.py:60` 把“尚不能说明”写成续稿必含词。它们既不证明当前路由可达，也会约束维护者保留否定模板。删断言，原稿、评审、manifest 与历史 commit 均保留。

## 方法级清单

A = 保留 Python 行为、打包元数据、历史证据结构/字节测试。B = 删除该测试方法（不删除它读取的历史证据）。C = 在同一方法中只删语义/措辞断言，保留其物理接口或字节部分。A 类的旧评测工具特别标明：仅为历史重放维护，不能充当本轮写作门。

### test_citation_audit.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `CitationAuditTests.test_marker_coverage_reports_n_over_m_without_claiming_semantic_support` (32–43) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_semicolons_inside_citations_preserve_coverage_in_three_variants` (45–53) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_sentence_semicolons_still_separate_claims_after_mixed_citations` (55–69) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_unparsed_ranges_report_high_structure_findings_in_three_variants` (71–84) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_partial_numeric_groups_keep_valid_mapping_and_report_unparsed_ranges` (86–93) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_range_budget_is_not_a_reference_number_ceiling` (95–102) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_numeric_scanning_preserves_reference_and_markdown_link_boundaries` (104–114) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_unparsed_ranges_fail_strict_without_an_implicit_coverage_threshold` (116–127) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_malformed_long_numeric_groups_complete_with_linear_scaling` (129–152) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_numeric_risk_matching_preserves_valid_number_contexts` (154–162) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_explicit_minimum_only_affects_strict_when_user_supplies_it` (164–185) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_numeric_mapping_duplicate_id_and_duplicate_doi_are_reported` (187–199) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_author_year_and_latex_count_as_coverage_without_fake_numeric_mapping` (201–210) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_reference_section_and_markdown_links_are_not_body_citations` (212–221) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_three_common_reference_headings_split_body_from_entries` (223–230) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_parenthetical_years_are_not_author_year_citations_in_three_variants` (232–242) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_generic_noun_year_pairs_are_not_narrative_citations` (244–262) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_narrative_author_year_citation_is_counted_and_author_is_preserved` (264–268) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_narrative_author_year_with_research_possessive_is_counted` (270–273) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_narrative_author_year_without_attribution_verb_is_counted` (275–278) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_named_project_can_remain_a_narrative_source` (280–283) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_own_study_statements_are_not_forced_to_take_external_citations` (285–294) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_cli_is_read_only_for_markdown_docx_and_stdin_and_rejects_fix` (296–344) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_script_itself_prevents_bytecode_writes_for_three_input_modes` (346–399) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `CitationAuditTests.test_text_report_uses_plain_n_over_m_display` (401–408) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |

### test_context_and_runtime.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `ContextAndRuntimeTests.test_runtime_directory_has_expected_files` (26–46) | A 保留 | 运行包物理文件集合；不是语义路由判定。 |
| `ContextAndRuntimeTests.test_entry_and_single_leaf_stay_within_character_budget` (48–53) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_entry_task_leaf_and_anti_ai_layer_stay_within_runtime_budget` (55–67) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_entry_task_leaf_and_citation_layer_stay_within_separate_phase_budget` (69–81) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_cross_cutting_layers_are_not_coloaded` (83–87) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_long_form_layer_is_progressive_and_not_loaded_for_short_work` (89–120) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_long_form_loading_precedence_resolves_crossing_conditions` (122–130) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_long_form_persistence_requires_write_authority` (132–143) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_leaf_bodies_do_not_embed_other_leaf_files` (145–148) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_fixture_has_twelve_unique_core_cases` (150–158) | A 保留 | 冻结夹具的 ID、数量、唯一性；不代表新候选写稿通过。 |
| `ContextAndRuntimeTests.test_short_review_minimum_does_not_reward_filler` (160–164) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |
| `ContextAndRuntimeTests.test_fixture_schema_and_route_mapping` (166–206) | C 拆分保留 | 保留 JSON 字段/类型/非空结构检查；删除 expected_route→expected_reference 的写作路由硬映射。 |
| `ContextAndRuntimeTests.test_fixture_covers_modes_material_states_and_protocols` (208–220) | B 删除断言/方法 | 锁入口/叶子字数、互斥加载、优先级、持久化话术、叶间指针禁令或写稿夹具的语义选择；改用真实路由观察和独立复核。 |

### test_final_body_lint.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `FinalBodyNegativeTailTests.test_unresolved_state_tail_flags_body_only_mode` (35–41) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_unresolved_state_tail_requires_sentence_final_position` (43–46) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_unresolved_state_tail_excludes_procedural_prefixes` (48–51) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_protective_negative_inference_flags_generic_denial` (53–57) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_protective_negative_inference_locates_two_clauses_in_one_sentence` (59–64) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_protective_negative_inference_locates_adjacent_sentences` (66–70) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_necessary_negative_facts_are_not_protective_inference` (72–75) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_negative_boundary_tail_is_low_candidate` (77–82) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_negative_tails_do_not_load_outside_final_body_modes` (84–96) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_body_with_suggestions_still_scans_body_area` (98–101) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyNegativeTailTests.test_quoted_material_is_not_scanned_as_final_body` (103–106) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `SignificanceTailClusterTests.test_three_hits_within_window_trigger_cluster` (119–124) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `SignificanceTailClusterTests.test_two_hits_do_not_trigger` (126–129) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `SignificanceTailClusterTests.test_heading_between_hits_resets_window` (131–139) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `SignificanceTailClusterTests.test_structure_flag_required` (141–144) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ExternalNoteHeadingTests.test_numbered_external_note_heading_flags_in_body_only` (148–152) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ExternalNoteHeadingTests.test_markdown_and_chapter_numbered_variants_flag` (154–162) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ExternalNoteHeadingTests.test_longer_business_heading_is_kept` (164–167) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ExternalNoteHeadingTests.test_generic_and_review_modes_skip_external_note_scan` (169–173) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ExternalNoteHeadingTests.test_suggestion_section_is_not_scanned` (175–178) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyReadOnlyAndOutputTests.test_input_file_is_never_modified` (182–190) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyReadOnlyAndOutputTests.test_json_output_carries_advice_and_pattern_fields` (192–202) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `FinalBodyReadOnlyAndOutputTests.test_cli_subprocess_smoke` (204–216) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |

### test_language_hygiene.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `LanguageHygieneTests.test_fixture_has_seven_complementary_cases` (214–235) | C 拆分保留 | 仅保留 H01–H07 数据集 ID 完整性；删除 semantic_focus 覆盖列表和 H06 固定文句断言。 |
| `LanguageHygieneTests.test_runtime_prompt_defines_contextual_local_rewrite_layer` (237–254) | B 删除断言/方法 | 直接 assertIn 当前 SKILL/ANTI-AI 十条措辞。 |
| `LanguageHygieneTests.test_candidate_frequency_is_observation_not_failure` (256–263) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_quote_match_is_reported_as_quoted_and_preserved` (265–271) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_hard_gate_blocks_missing_invariant_and_explicit_leak` (273–278) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_review_only_mode_requires_review_fields` (280–284) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_rewrite_mode_rejects_complete_review_table` (286–293) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_prompt_fix_requires_three_outputs_two_cases_two_writers` (295–327) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_strict_evidence_accepts_two_writers_and_two_blind_verifiers_read_only` (329–380) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_verifier_hard_failure_blocks_evidence` (382–395) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_any_five_dimension_failure_blocks_evidence` (397–408) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_prompt_only_inputs_are_exact_unique_and_relative` (410–433) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `LanguageHygieneTests.test_strict_git_binding_rejects_dirty_protected_candidate` (435–459) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |

### test_long_form_evidence.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `LongFormEvidenceTests.test_research_records_borrowed_and_rejected_patterns` (12–23) | B 删除断言/方法 | 对旧研究报告/稿件/评审硬断言文句、篇幅、结论；保留全部历史证据，不再把这些文字当软件门禁。 |
| `LongFormEvidenceTests.test_full_review_finds_seeded_hard_and_global_conflicts` (25–40) | B 删除断言/方法 | 对旧研究报告/稿件/评审硬断言文句、篇幅、结论；保留全部历史证据，不再把这些文字当软件门禁。 |
| `LongFormEvidenceTests.test_continuation_preserves_state_and_prompt_range` (42–72) | B 删除断言/方法 | 对旧研究报告/稿件/评审硬断言文句、篇幅、结论；保留全部历史证据，不再把这些文字当软件门禁。 |
| `LongFormEvidenceTests.test_baseline_comparison_does_not_claim_candidate_superiority` (74–91) | B 删除断言/方法 | 对旧研究报告/稿件/评审硬断言文句、篇幅、结论；保留全部历史证据，不再把这些文字当软件门禁。 |

### test_manuscript_audit.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `ManuscriptAuditTests.test_cross_file_candidates_and_latex_errors_are_separated` (28–46) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_term_and_abbreviation_checks_are_opt_in` (48–52) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_same_line_abbreviation_before_definition_is_reported` (54–59) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_nested_term_variants_do_not_double_count_one_occurrence` (61–66) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_latex_comments_and_code_are_ignored_but_reference_variants_are_checked` (68–82) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_heading_without_blank_line_does_not_hide_duplicate_prose` (84–89) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_longer_closing_fences_and_unclosed_blocks_hide_example_refs` (91–97) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_fence_marker_length_and_closing_suffix_preserve_boundaries` (99–107) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_invalid_backtick_info_does_not_hide_following_prose` (109–112) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_fence_in_latex_literal_does_not_hide_following_real_reference` (114–120) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_fake_latex_opener_in_fence_does_not_consume_following_literal` (122–129) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_commented_or_inline_latex_begin_does_not_disable_fence_protection` (131–137) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_comment_character_in_literal_does_not_hide_next_environment` (139–143) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_fence_mask_preserves_offsets_for_lf_crlf_and_cr` (145–153) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_strict_cli_ignores_fenced_examples_but_checks_following_prose` (155–165) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_strict_only_fails_high_structural_findings` (167–191) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ManuscriptAuditTests.test_cli_is_json_report_only_and_rejects_fix` (193–221) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |

### test_output_checker.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `OutputCheckerTests.test_all_twelve_cases_load` (27–28) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_verifier_schema_covers_adherence_and_orchestration` (30–34) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_accepts_preserved_literals` (36–42) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_rejects_missing_immutable_literal` (44–48) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_rejects_exact_forbidden_claim` (50–54) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_does_not_block_ordinary_negative_explanation` (56–63) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_rejects_non_object_manifest_without_crashing` (65–71) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_checker_rejects_evidence_path_escape` (73–77) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_case_loader_rejects_null_without_traceback` (79–84) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_blind_row_with_unhashable_writer_id_is_controlled` (86–132) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_file_hash_uses_raw_bytes` (134–139) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_cli_rejects_cases_directory_without_traceback` (141–156) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |
| `OutputCheckerTests.test_context_ablation_rejects_reused_output_and_context` (158–219) | A 保留 | 实际测试保留的旧证据工具函数/CLI；只维护该 Python 行为，不将其 CHECK/PASS、词频或固定评审阈值接为新写稿门禁。 |

### test_paragraph_ablation_evidence.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `ParagraphAblationEvidenceTests.test_anonymous_maps_cover_each_arm_once_per_task` (13–19) | A 保留 | 匿名映射完整性，属于历史证据结构。 |
| `ParagraphAblationEvidenceTests.test_frozen_tasks_packets_and_verdicts_are_complete` (21–32) | C 拆分保留 | 保留 T1–T3/A–C 匿名样本标识存在；删除评审必须包含 PASS、FAIL、篇幅的词面断言。 |
| `ParagraphAblationEvidenceTests.test_repair_is_pre_registered_as_one_shot` (34–37) | B 删除断言/方法 | 锁历史复测计划的具体措辞；计划原件保留。 |
| `ParagraphAblationEvidenceTests.test_repair_blind_map_and_verdicts_are_complete` (39–46) | C 拆分保留 | 保留映射覆盖；删除判决必须出现 PASS、FAIL 的词面断言。 |

### test_prompt_gate_provider_matrix.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `PromptGateProviderMatrixTests.test_schedule_is_three_provider_twenty_one_call_matrix` (23–30) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_replication_and_route_schedules_are_explicit` (32–44) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_crossing_condition_schedule_is_twelve_paired_calls` (46–65) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_pair_order_is_balanced_across_providers` (67–75) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_filtered_persistence_schedule_has_nine_calls` (77–83) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_skill_fingerprint_binds_relative_paths_and_bytes` (85–93) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_reports_each_exact_skill_relative_path` (95–116) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_supports_absolute_windows_path_and_rejects_failed_read` (118–142) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_supports_cat_and_direct_get_content` (144–152) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_supports_safe_get_content_options_before_path` (154–162) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_rejects_unknown_get_content_option_prefix` (164–171) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_observed_reads_rejects_echo_and_compound_commands` (173–181) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_bypass_scope_rejects_non_persistence_task` (183–197) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_bypass_scope_accepts_authorized_review_persistence_task` (199–212) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |
| `PromptGateProviderMatrixTests.test_build_prompt_does_not_expose_arm_or_expected_behavior` (214–221) | A 保留 | 实际测试历史 harness 的调度、盲化、读工具记录解析、路径/字节或授权行为；不是解析 Markdown 路由语义。 |

### test_prose_lint.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `ProseLintTests.test_semantic_patterns_are_candidates_not_hard_failures` (27–36) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_quotes_formulas_citations_and_references_are_protected` (38–49) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_frequency_counts_visible_body_without_forcing_replacement` (51–57) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_latex_body_environments_leave_residues_visible` (59–67) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_latex_math_code_and_quotes_remain_protected` (69–81) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_latex_protection_ends_only_at_the_matching_environment` (83–98) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_numeric_citation_protection_preserves_marker_forms_and_long_numbers` (100–111) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_protected_latex_delimiters_do_not_hide_following_prose` (113–127) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_protected_delimiters_do_not_close_active_math_or_quotes` (129–140) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_quote_lookahead_ignores_protected_closing_delimiters` (142–151) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_malformed_numeric_markers_do_not_become_protected` (153–156) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_long_malformed_numeric_markers_finish_within_cli_timeout` (158–172) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_body_with_suggestions_excludes_suggestion_term_frequency` (174–182) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_delivery_residues_have_three_independent_variants` (184–193) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_legitimate_academic_terms_and_suggestion_heading_are_not_residues` (195–198) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_protected_urls_and_paths_do_not_hide_following_prose_three_variants` (200–208) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_legitimate_academic_context_is_not_high_residue` (210–221) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_scanning_resumes_after_references_for_three_post_sections` (223–232) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_format_and_structure_candidates_are_reported` (234–246) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_review_only_does_not_treat_quoted_problem_text_as_own_style` (248–251) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_docx_reads_only_main_body` (253–283) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_cli_is_read_only_json_capable_and_strict_only_when_requested` (285–323) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |
| `ProseLintTests.test_missing_file_returns_controlled_error` (325–334) | A 保留 | 实际调用运行 Python 扫描器，检验候选定位、保护区、CLI/只读/strict 或性能；不据 finding 判稿件优劣。 |

### test_public_log_sanitizer.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `PublicLogSanitizerTests.test_redacts_internal_url_path_and_opaque_keys` (23–34) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `PublicLogSanitizerTests.test_unrelated_stderr_is_unchanged` (36–38) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `PublicLogSanitizerTests.test_check_covers_markdown_and_json_not_only_stderr` (40–44) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `PublicLogSanitizerTests.test_apply_backs_up_and_propagates_nested_hash_references` (46–80) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |

### test_release_policy.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `ReleasePolicyTests.test_three_release_targets_are_declared` (42–48) | C 拆分保留 | 保留 machine policy 的平台数组/排除项；删除 HANDOFF 固定汉语串，README 平台 URL 可保留为元数据链接。 |
| `ReleasePolicyTests.test_project_and_skillhub_metadata_use_mit` (50–63) | C 拆分保留 | 保留许可证内容一致、machine license/channel 约束；删除 README 分节后必须只等于 [MIT](LICENSE) 的排版断言。 |
| `ReleasePolicyTests.test_real_writing_precedes_engineering_gates` (65–71) | B 删除断言/方法 | 直接锁 README/HANDOFF 迭代措辞，且强迫语义收益后继续补 Python 门，与本轮授权相反。 |
| `ReleasePolicyTests.test_public_copy_does_not_expose_release_commands` (73–82) | B 删除断言/方法 | README/HANDOFF 文案黑名单，既非凭据扫描也非打包边界；不该限制维护说明使用真实命令。 |
| `ReleasePolicyTests.test_skillhub_frontmatter_is_minimal_and_has_no_homepage` (84–100) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_skillhub_package_is_eleven_runtime_files_plus_markdown_license` (102–118) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_repository_and_local_surfaces_cannot_enter_skillhub_package` (120–145) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_v008_clawhub_release_remains_a_historical_fact` (147–150) | B 删除断言/方法 | 锁历史说明的具体汉语表述；历史段落及回执原件继续保留。 |
| `ReleasePolicyTests.test_current_release_copy_matches_the_package_and_evidence_boundary` (152–166) | C 拆分保留 | 保留已发布版本 badge/install ID 与当前包元数据一致；删除旧版本收益、字数和边界说明的七条 assertIn。 |
| `ReleasePolicyTests.test_v009_public_receipt_binds_both_release_surfaces` (168–192) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_v010_public_receipt_binds_package_icon_and_pending_review` (194–225) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_v011_public_receipt_binds_three_release_surfaces` (227–264) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_v012_public_receipt_binds_three_release_surfaces` (266–303) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |
| `ReleasePolicyTests.test_v013_public_receipt_binds_three_release_surfaces` (305–348) | A 保留 | 打包白名单、平台元数据或固定发布回执绑定；不判写作语义。 |

### test_skill_contract.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `SkillContractTests.test_frontmatter_has_only_name_and_description` (52–60) | C 拆分保留 | 保留 frontmatter 字段、slug 及 description 非空；删除 >40 字符与四条正反向措辞断言。 |
| `SkillContractTests.test_openai_metadata_uses_new_invocation_name` (62–68) | A 保留 | 宿主显示名与合法 skill 调用 ID 属于包元数据/安装入口契约。 |
| `SkillContractTests.test_four_dimensional_route_and_nested_routes_are_explicit` (70–78) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_nonacademic_artifact_stops_and_transfers` (80–88) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_user_facing_copy_hides_process_and_audience_labels` (90–97) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_final_copy_check_removes_repeated_explanations_and_tail_notes` (99–107) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_material_gates_are_explicit` (109–120) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_evidence_and_citation_contract_is_explicit` (122–132) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_citation_research_is_explicitly_authorized_and_progressive` (134–145) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_default_citation_style_distinguishes_rich_text_from_markdown` (147–156) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_source_authority_and_coverage_contract_is_not_a_black_box_score` (158–167) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_citation_identity_and_atomic_claim_contract_are_explicit` (169–185) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_post_writing_semantic_gate_precedes_citation_formatting` (187–199) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_publication_status_check_never_upgrades_missing_records` (201–212) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_integrity_standards_and_review_interface_are_explicit` (214–222) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_optional_post_text_suggestion_categories_are_centralized` (224–233) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_leaf_specific_contracts_exist_without_global_rule_copies` (235–274) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_anti_ai_reference_is_progressive_cross_cutting_layer` (276–295) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_anti_ai_loading_precedence_is_deterministic` (297–305) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_protective_expansion_review_is_delete_only_and_bounded` (307–320) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_iteration_policy_uses_real_outputs_and_terminal_decisions` (322–331) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_academic_inference_is_bounded_without_becoming_source_literalism` (333–345) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_v160_continuous_negation_rule_is_position_independent` (347–357) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_final_delivery_boundary_is_positive_and_keeps_exception` (359–367) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_review_contract_keeps_fields_but_allows_scale_appropriate_forms` (369–376) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_long_form_state_and_global_review_contract_is_explicit` (378–396) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_manuscript_audit_is_read_only_and_candidate_only` (398–409) | B 删除断言/方法 | 源代码英文说明/参数词存在不是行为证明；只读、CLI 与结构性 strict 已由 test_manuscript_audit.py 实测承接。 |
| `SkillContractTests.test_sample_identity_cannot_be_inferred_from_context` (411–413) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_process_leak_exceptions_never_cover_the_models_own_workflow` (415–419) | B 删除断言/方法 | 对当前 SKILL/reference/维护说明作固定词句、反向禁词或语义规则断言；由真实写稿与宿主独立评审验证。 |
| `SkillContractTests.test_prose_lint_is_report_only_and_academically_adapted` (421–431) | B 删除断言/方法 | 英文说明/公文词汇黑名单锁源码措辞；只读、CLI、候选不硬失败已由 test_prose_lint.py 实测承接。 |
| `SkillContractTests.test_citation_audit_is_read_only_and_has_no_default_quota` (433–443) | B 删除断言/方法 | 英文 docstring/源码词存在不是行为证明；只读、无默认配额、无 pyc 已由 test_citation_audit.py 实测承接。 |
| `SkillContractTests.test_runtime_prompt_has_no_version_or_legacy_invocation` (445–450) | C 拆分保留 | 删除正文不得出现 0.0.1 的任意字符串限制；可保留失效调用 ID 检查，或由现有 metadata 测试承接。 |

### test_skillhub_package_builder.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `SkillHubPackageBuilderTests.test_build_is_minimal_metadata_valid_and_deterministic` (41–110) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `SkillHubPackageBuilderTests.test_invalid_version_and_existing_destination_fail_closed` (112–148) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `SkillHubPackageBuilderTests.test_policy_rejects_traversal_absolute_and_reserved_paths` (150–173) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `SkillHubPackageBuilderTests.test_zip_inside_package_is_rejected_without_creating_output` (175–196) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `SkillHubPackageBuilderTests.test_existing_or_failed_zip_never_leaves_a_package_directory` (198–230) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |
| `SkillHubPackageBuilderTests.test_generated_icon_is_github_only_square_png` (232–241) | A 保留 | Python 打包/脱敏真实行为、安全边界、原子写入或哈希验证。 |

### test_v002_sanity_evidence.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `Version002SanityEvidenceTests.test_fixture_and_historical_runtime_hashes_are_sealed` (54–80) | A 保留 | 历史 commit 与冻结输入哈希校验。 |
| `Version002SanityEvidenceTests.test_two_fresh_writers_cover_all_cases` (82–96) | C 拆分保留 | 保留 writer/sample/case ID、数量、盲审先后记录；删除读取旧稿后逐字 required/forbidden 断言。 |
| `Version002SanityEvidenceTests.test_review_only_outputs_use_the_five_column_contract` (98–106) | B 删除断言/方法 | 旧真实稿必须采用五列表头及不得出现某词，属于写稿形式硬断言。 |
| `Version002SanityEvidenceTests.test_blind_verifier_passes_adherence_and_orchestration` (108–127) | C 拆分保留 | 保留 blind 与 results 数量等封存结构；删除 overall/各维度必须 PASS、hard_failures 空及 3/2/2 修改阈值硬断言。 |

### test_v003_citation_sanity.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `Version003CitationSanityTests.test_fixture_and_twelve_raw_outputs_are_sealed_to_candidate` (49–59) | A 保留 | 冻结 fixture、12 稿与历史 commit 的字节绑定。 |
| `Version003CitationSanityTests.test_two_continuous_writers_report_only_the_authorized_web_turn` (61–70) | A 保留 | 保留历史工具使用/精确未知模型标记与上下文证据；不得用于证明当前宿主执行。 |
| `Version003CitationSanityTests.test_outputs_follow_source_layers_modes_and_default_citation_style` (72–111) | B 删除断言/方法 | 旧真实稿必须出现 未读取/不能支持/不能或无法、特定引用样式与固定篇幅；直接强化被用户质疑的否定表达。 |
| `Version003CitationSanityTests.test_final_outputs_have_complete_reference_mapping_and_only_review_candidates` (113–124) | A 保留 | 实际调用当前 citation_audit 对固定稿件验证标记映射与结构 finding；这是 Python 回归样本，绝不证明稿件语义正确。 |
| `Version003CitationSanityTests.test_two_cold_verifiers_have_no_hard_or_common_failure` (126–136) | C 拆分保留 | 保留两名 verifier、blind/model_id/样本结构；删除固定 PASS/WARN/FAIL 分布、hard_failures 为空及语义阈值结论。 |

### test_v003_live_citation.py

| 方法（原行号） | 处置 | 理由 / 最小变动 |
| --- | --- | --- |
| `Version003LiveCitationTests.test_raw_live_outputs_and_cold_verdict_are_sealed` (13–17) | C 拆分保留 | 保留每个冻结文件 SHA-256；删除 manifest.verdict 必须 FAIL 的语义结果断言，历史 FAIL 仍在原证据中。 |
| `Version003LiveCitationTests.test_default_offline_and_metadata_only_boundaries_hold` (19–26) | B 删除断言/方法 | 从历史稿件或判决抽取固定词句/引用格式，语义判定留原始独立评审。 |
| `Version003LiveCitationTests.test_retrieval_and_numeric_mapping_cover_four_real_dois` (28–36) | B 删除断言/方法 | 从历史稿件或判决抽取固定词句/引用格式，语义判定留原始独立评审。 |
| `Version003LiveCitationTests.test_cold_review_preserves_semantic_failures` (38–43) | B 删除断言/方法 | 从历史稿件或判决抽取固定词句/引用格式，语义判定留原始独立评审。 |

## 工具、调用关系和最小调整

| 文件 | 处置 | 依赖 / 调用者与理由 |
| --- | --- | --- |
| `tools/build_skillhub_package.py` | A 全部保留 | `test_skillhub_package_builder.py` 导入，发布手工调用。SemVer、frontmatter 字段、slug 一致、许可、白名单、路径安全、确定性 ZIP 都是打包接口。检查 YAML 字段形状不是 Markdown 语义门；不要删除 `render_skill_md` 的必要字段检查。 |
| `tools/skillhub-package-policy.json` | A 保留 | builder 与 release policy 测试读取；维护文件白名单、平台和许可证。若新增叶子，只更新白名单及包数量，不新增叶路由语义解析器。 |
| `tools/sanitize_public_eval_logs.py` | A 全部保留 | `test_public_log_sanitizer.py` 导入。隐私脱敏、备份、原子替换、嵌套哈希传播是 Python 维护职责；本轮不运行 apply，不改历史证据字节。 |
| `tools/check_academic_outputs.py` | 保留作历史重放；卸下新写稿必经门 | `test_output_checker.py` 导入；`test_context_and_runtime.py` 使用同类 fixture。`check_output` (190–210) 逐字检查旧夹具的最少字数、required_markers 和 forbidden_claims；`validate_dimension_record` (337–353)、`validate_evidence` (574–977) 把独立评审 FAIL/BLOCK 转 CHECK=FAIL、且 strict 要求固定 writer/verifier 数量。这不能作为当前 Markdown 质量门。最小调整：docstring/帮助明确“旧证据重放、非当前写稿或规则发布门”；从现行维护流程撤下 strict 必经要求，保留现有函数和行为测试，不另造语义替代器。 |
| `tools/check_language_hygiene_outputs.py` | 保留作历史重放；卸下新写稿必经门 | `test_language_hygiene.py` 导入。`check_output` (266–290) 将固定 review 字段词面作为硬门；`FIX_THRESHOLD` (41–45)、`summarize_prompt_fix_candidates` (377–399)、`validate_evidence` (416–802) 固化 3/2/2 及评审判词；这些只解释历史实验。最小同上，不能把 `PROMPT_FIX_RECOMMENDATIONS` 当本轮规则接受器；哈希、相对路径、匿名绑定和 JSON 错误处理继续测试。 |

`rg` 在现行 Python/PowerShell 源码中未找到两个 evidence checker 被其他 runner 调用（除上述单元测试）。它们并非 runtime 运行依赖；真正把它们提升为必经门的是 HANDOFF 的维护文字。不要为“卸下门禁”而重构约 1,900 行旧工具或改写历史 evidence 脚本。若父任务决定彻底废弃旧工具 CLI，那属于另一个 Python API 删除动作，需要同时处理所有调用者；本轮没有必要。

`test_prompt_gate_provider_matrix.py` 实际导入 `tests/evidence/prompt-gates-20260812/run_provider_matrix.py`，测试 schedule/skill_fingerprint/observed_reads/validate_bypass_scope/build_prompt。`observed_reads` 解析实际工具调用日志，既有能力可用作真实写稿的加载证据；不要扩写为根据 SKILL 文义计算可达性的路由解析器。`build_prompt` 的 arm 不泄露断言是盲化接口安全，非优劣路线或要求正文出现某句。

若保留 `tests/test_skill_contract.py` 中 2–3 个元数据方法，就无需修改 `check_academic_outputs.py:32–38` 的 PROTECTED_PATHS。若整文件删除，必须同步移除其保护列表路径，否则新制 evidence 会出现悬挂保护路径；过去 manifest 引用该文件的历史 commit 与 hash 保持原样。类似地，`check_language_hygiene_outputs.py:26–38` 绑定自身测试与 runtime 旧文件列表；它解释历史 schema，不应随新叶子扩充成当前规则门。

## README、HANDOFF 与 CI

仓库 `git ls-files .github/*` 无输出；未发现跟踪的 GitHub Actions、Makefile、pyproject/tox 配置。不要声称已从 CI 移除原本不存在的门，也无需为这次清理新建 CI。现行测试入口是手动 `python -B -m unittest discover -s tests -v`。

- README 第 74–78 行“迭代原则”：保留真实写稿和差异归因；将“收益后补最小确定性测试和发布门”改成明确两类：Markdown 规则以新鲜正文和宿主独立复核决定，Python 实现才运行相应最小测试/打包与安全检查。不能继续把任何语义修订默认转换成词句断言。
- HANDOFF “迭代顺序”第 3 条：同样拆开 Markdown 与 Python；“合并/取消”、样本不足继续真实写稿可以保持，3/2/2 等旧阈值只作为历史设计，不作为当前语义修改的强制数字门。
- HANDOFF “后续线程应先做的工作”第 3 条：删除普遍要求“结构校验、严格证据检查”随每次 Markdown 调整运行的表述；改为“真实写稿由独立宿主 subagent 复核；Python/打包改动运行相关最小测试，证据文件可做字节完整性验证”。
- HANDOFF 同节第 7 条：将 Prompt 文风评审交给独立复核、关注 AI 味/结构/逻辑/重复/流水账及材料范围；保留确定性 Python 缺陷的输入复现和回归要求。不要把旧 3/2/2 计数写成新 Python 门；用户授权本轮由实稿判断。
- README 第 38 行“先完成内容证据复核、再按需检查”应与独立复核层一起改写，明确有 harness subagent 时由未写该稿的宿主子代理复核；扫描器只提供位置候选。历史版本段落不要为了新规范重写过去事实或把旧测试数量改成新数量。

## 最小实施与验证

1. 按上表删 B、拆 C，A 保持。清掉失去使用的 `re`、READMEs、reference 全量读取等 setUpClass 变量；不要新增替代字符串门、Markdown 路由解析器或“删除语义测试成功”的测试。
2. 只更新当前 README/HANDOFF 维护要求及两个旧 checker 的用途说明；全部 `tests/evidence/**` 和历史 manifest 原样保存。
3. 运行 `py -3 -B -m unittest discover -s tests -v`，结果标为 Python、打包与历史证据维护测试，不声称通过等于 Markdown 写作质量通过。
4. Markdown 规则验证另交当前候选的新鲜实际稿件及独立宿主 reviewer；路由完整性应审真实加载轨迹、分段范围与结束条件。
5. 此子任务未运行测试：没有改动实现或测试，工作是只读方法级审计；最终编辑者须运行上面的保留测试集合。

方法数量：219；A=153, B=53, C=13。C 为逐断言拆分，最终测试数量由实际保留方法决定，不按旧 219 数量补齐。
