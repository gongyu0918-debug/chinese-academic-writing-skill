# Python 维护边界落实结果

已落实审计报告：删除 53 个方法、拆分 13 个方法，保留 153 个完整方法及拆分后的 13 个方法，共 166 项。删除全为语义断言的 `tests/test_long_form_evidence.py`；它引用的历史原稿和报告没有删除。

README/HANDOFF 当前维护要求已明确：Markdown 规则只以新鲜实际成稿和独立语义复核验证；Python 实现、CLI、安全、性能、打包继续运行相关测试。两个历史 checker 的模块说明/CLI 帮助标为 legacy，其可执行 AST 与 HEAD 相同，现有行为测试继续保留。

`git diff --name-only -- tests/evidence chinese-academic-writing-assistant/scripts` 无输出。未修改七份写作 Markdown；这些文件在接手本子任务前已有主任务改动。没有新增语义测试、路由解析器或 CI。

验证：`py -3 -B -m unittest discover -s tests -v` → **166/166 PASS**，8.898 秒，无失败/错误；`git diff --check` 无错误。日志 `.release/test-boundary-final-tests.log`，SHA-256 `ccafe931e461fbf9958ee5e59eb10665974e9f83c8f9057186b4431c20e780f7`。这些结果验证 Python 维护边界，不代表 Markdown 写作质量通过。

尚未 commit，按主任务要求等待统一整合。实际写稿和独立评审由主任务继续负责。

## 删除的方法

- `test_context_and_runtime.py:test_entry_and_single_leaf_stay_within_character_budget`
- `test_context_and_runtime.py:test_entry_task_leaf_and_anti_ai_layer_stay_within_runtime_budget`
- `test_context_and_runtime.py:test_entry_task_leaf_and_citation_layer_stay_within_separate_phase_budget`
- `test_context_and_runtime.py:test_cross_cutting_layers_are_not_coloaded`
- `test_context_and_runtime.py:test_long_form_layer_is_progressive_and_not_loaded_for_short_work`
- `test_context_and_runtime.py:test_long_form_loading_precedence_resolves_crossing_conditions`
- `test_context_and_runtime.py:test_long_form_persistence_requires_write_authority`
- `test_context_and_runtime.py:test_leaf_bodies_do_not_embed_other_leaf_files`
- `test_context_and_runtime.py:test_short_review_minimum_does_not_reward_filler`
- `test_context_and_runtime.py:test_fixture_covers_modes_material_states_and_protocols`
- `test_language_hygiene.py:test_runtime_prompt_defines_contextual_local_rewrite_layer`
- `test_long_form_evidence.py:test_research_records_borrowed_and_rejected_patterns`
- `test_long_form_evidence.py:test_full_review_finds_seeded_hard_and_global_conflicts`
- `test_long_form_evidence.py:test_continuation_preserves_state_and_prompt_range`
- `test_long_form_evidence.py:test_baseline_comparison_does_not_claim_candidate_superiority`
- `test_paragraph_ablation_evidence.py:test_repair_is_pre_registered_as_one_shot`
- `test_release_policy.py:test_real_writing_precedes_engineering_gates`
- `test_release_policy.py:test_public_copy_does_not_expose_release_commands`
- `test_release_policy.py:test_v008_clawhub_release_remains_a_historical_fact`
- `test_skill_contract.py:test_four_dimensional_route_and_nested_routes_are_explicit`
- `test_skill_contract.py:test_nonacademic_artifact_stops_and_transfers`
- `test_skill_contract.py:test_user_facing_copy_hides_process_and_audience_labels`
- `test_skill_contract.py:test_final_copy_check_removes_repeated_explanations_and_tail_notes`
- `test_skill_contract.py:test_material_gates_are_explicit`
- `test_skill_contract.py:test_evidence_and_citation_contract_is_explicit`
- `test_skill_contract.py:test_citation_research_is_explicitly_authorized_and_progressive`
- `test_skill_contract.py:test_default_citation_style_distinguishes_rich_text_from_markdown`
- `test_skill_contract.py:test_source_authority_and_coverage_contract_is_not_a_black_box_score`
- `test_skill_contract.py:test_citation_identity_and_atomic_claim_contract_are_explicit`
- `test_skill_contract.py:test_post_writing_semantic_gate_precedes_citation_formatting`
- `test_skill_contract.py:test_publication_status_check_never_upgrades_missing_records`
- `test_skill_contract.py:test_integrity_standards_and_review_interface_are_explicit`
- `test_skill_contract.py:test_optional_post_text_suggestion_categories_are_centralized`
- `test_skill_contract.py:test_leaf_specific_contracts_exist_without_global_rule_copies`
- `test_skill_contract.py:test_anti_ai_reference_is_progressive_cross_cutting_layer`
- `test_skill_contract.py:test_anti_ai_loading_precedence_is_deterministic`
- `test_skill_contract.py:test_protective_expansion_review_is_delete_only_and_bounded`
- `test_skill_contract.py:test_iteration_policy_uses_real_outputs_and_terminal_decisions`
- `test_skill_contract.py:test_academic_inference_is_bounded_without_becoming_source_literalism`
- `test_skill_contract.py:test_v160_continuous_negation_rule_is_position_independent`
- `test_skill_contract.py:test_final_delivery_boundary_is_positive_and_keeps_exception`
- `test_skill_contract.py:test_review_contract_keeps_fields_but_allows_scale_appropriate_forms`
- `test_skill_contract.py:test_long_form_state_and_global_review_contract_is_explicit`
- `test_skill_contract.py:test_manuscript_audit_is_read_only_and_candidate_only`
- `test_skill_contract.py:test_sample_identity_cannot_be_inferred_from_context`
- `test_skill_contract.py:test_process_leak_exceptions_never_cover_the_models_own_workflow`
- `test_skill_contract.py:test_prose_lint_is_report_only_and_academically_adapted`
- `test_skill_contract.py:test_citation_audit_is_read_only_and_has_no_default_quota`
- `test_v002_sanity_evidence.py:test_review_only_outputs_use_the_five_column_contract`
- `test_v003_citation_sanity.py:test_outputs_follow_source_layers_modes_and_default_citation_style`
- `test_v003_live_citation.py:test_default_offline_and_metadata_only_boundaries_hold`
- `test_v003_live_citation.py:test_retrieval_and_numeric_mapping_cover_four_real_dois`
- `test_v003_live_citation.py:test_cold_review_preserves_semantic_failures`

## 拆分的方法（原名）

- `test_context_and_runtime.py:test_fixture_schema_and_route_mapping`
- `test_language_hygiene.py:test_fixture_has_seven_complementary_cases`
- `test_paragraph_ablation_evidence.py:test_frozen_tasks_packets_and_verdicts_are_complete`
- `test_paragraph_ablation_evidence.py:test_repair_blind_map_and_verdicts_are_complete`
- `test_release_policy.py:test_three_release_targets_are_declared`
- `test_release_policy.py:test_project_and_skillhub_metadata_use_mit`
- `test_release_policy.py:test_current_release_copy_matches_the_package_and_evidence_boundary`
- `test_skill_contract.py:test_frontmatter_has_only_name_and_description`
- `test_skill_contract.py:test_runtime_prompt_has_no_version_or_legacy_invocation`
- `test_v002_sanity_evidence.py:test_two_fresh_writers_cover_all_cases`
- `test_v002_sanity_evidence.py:test_blind_verifier_passes_adherence_and_orchestration`
- `test_v003_citation_sanity.py:test_two_cold_verifiers_have_no_hard_or_common_failure`
- `test_v003_live_citation.py:test_raw_live_outputs_and_cold_verdict_are_sealed`
