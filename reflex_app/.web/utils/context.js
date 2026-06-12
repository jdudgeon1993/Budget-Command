import { createContext, useContext, useMemo, useReducer, useState, createElement, useEffect } from "react"
import { applyDelta, ReflexEvent, hydrateClientStorage, useEventLoop, refs } from "$/utils/state"
import { jsx } from "@emotion/react";

export const initialState = {"reflex___state____state": {"is_hydrated_rx_state_": false, "router_rx_state_": {"session": {"client_token": "", "client_ip": "", "session_id": ""}, "headers": {"host": "", "origin": "", "upgrade": "", "connection": "", "cookie": "", "pragma": "", "cache_control": "", "user_agent": "", "sec_websocket_version": "", "sec_websocket_key": "", "sec_websocket_extensions": "", "accept_encoding": "", "accept_language": "", "raw_headers": {}}, "page": {"host": "", "path": "", "raw_path": "", "full_path": "", "full_raw_path": "", "params": {}}, "url": {"scheme": "", "netloc": "", "origin": "://", "path": "", "query": "", "query_parameters": {}, "fragment": "", "href": ""}, "route_id": ""}}, "reflex___state____state.cura___state____app_state": {"access_token_rx_state_": "", "account_options_rx_state_": [], "accounts_rows_rx_state_": [], "acct_balance_map_rx_state_": {}, "acct_expanded_id_rx_state_": "", "acct_ledger_rows_rx_state_": [], "acct_settings_aid_rx_state_": "", "acct_settings_apr_rx_state_": "", "acct_settings_color_rx_state_": "#3a7fc1", "acct_settings_credit_rx_state_": "", "acct_settings_error_rx_state_": "", "acct_settings_is_promo_rx_state_": false, "acct_settings_min_pay_rx_state_": "", "acct_settings_name_rx_state_": "", "acct_settings_open_rx_state_": false, "acct_settings_opening_rx_state_": "0", "acct_settings_promo_end_rx_state_": "", "acct_settings_saving_rx_state_": false, "acct_settings_type_rx_state_": "budget", "active_mid_rx_state_": "", "active_panel_rx_state_": "buckets", "add_acct_color_rx_state_": "#3a7fc1", "add_acct_error_rx_state_": "", "add_acct_name_rx_state_": "", "add_acct_open_rx_state_": false, "add_acct_opening_rx_state_": "0", "add_acct_saving_rx_state_": false, "add_acct_type_rx_state_": "budget", "add_bkt_cat_id_rx_state_": "", "add_bkt_creating_cat_rx_state_": false, "add_bkt_name_rx_state_": "", "add_bkt_new_cat_color_rx_state_": "#818cf8", "add_bkt_new_cat_name_rx_state_": "", "add_bkt_saving_rx_state_": false, "add_bkt_type_rx_state_": "expense", "alloc_fmt_rx_state_": "$0.00", "alloc_pct_rx_state_": 0, "alloc_rule_rows_rx_state_": [], "archived_cat_rows_rx_state_": [], "attention_rows_rx_state_": [], "auth_error_rx_state_": "", "bsettings_bid_rx_state_": "", "bsettings_open_rx_state_": false, "bsf_budget_rx_state_": "", "bsf_cat_id_rx_state_": "", "bsf_contrib_freq_rx_state_": "", "bsf_due_amount_rx_state_": "", "bsf_due_day_rx_state_": "", "bsf_error_rx_state_": "", "bsf_name_rx_state_": "", "bsf_notes_rx_state_": "", "bsf_pay_freq_rx_state_": "", "bsf_recurring_rx_state_": false, "bsf_release_amt_rx_state_": "", "bsf_rollover_rx_state_": false, "bsf_saving_rx_state_": false, "bsf_skip_rx_state_": false, "bsf_target_amount_rx_state_": "", "bsf_target_date_rx_state_": "", "bsf_transfer_amt_rx_state_": "", "bsf_transfer_bid_rx_state_": "", "bsf_type_rx_state_": "expense", "bsf_vault_total_rx_state_": 0.0, "bsf_vault_total_fmt_rx_state_": "$0.00", "bucket_rows_rx_state_": [], "bva_month_hdrs_rx_state_": [], "bva_rows_rx_state_": [], "cat_edit_color_rx_state_": "", "cat_edit_id_rx_state_": "", "cat_edit_name_rx_state_": "", "cat_options_rx_state_": [], "cat_rollup_rows_rx_state_": [], "cat_rows_rx_state_": [], "cat_saving_rx_state_": false, "close_month_saving_rx_state_": false, "copy_allocs_saving_rx_state_": false, "debt_pay_acct_name_rx_state_": "", "debt_pay_aid_rx_state_": "", "debt_pay_amount_rx_state_": "", "debt_pay_bucket_rx_state_": "", "debt_pay_date_rx_state_": "", "debt_pay_error_rx_state_": "", "debt_pay_from_account_rx_state_": "", "debt_pay_open_rx_state_": false, "debt_pay_saving_rx_state_": false, "debt_tracker_rows_rx_state_": [], "distribute_visible_rx_state_": false, "edit_alloc_val_rx_state_": "", "edit_budget_val_rx_state_": "", "edit_pc_amount_rx_state_": "", "edit_pc_anchor_rx_state_": "", "edit_pc_error_rx_state_": "", "edit_pc_freq_rx_state_": "14", "edit_pc_id_rx_state_": "", "edit_pc_label_rx_state_": "", "edit_pc_open_rx_state_": false, "edit_pc_saving_rx_state_": false, "edit_tx_account_rx_state_": "", "edit_tx_amount_rx_state_": "", "edit_tx_bucket_rx_state_": "", "edit_tx_date_rx_state_": "", "edit_tx_desc_rx_state_": "", "edit_tx_error_rx_state_": "", "edit_tx_id_rx_state_": "", "edit_tx_income_type_rx_state_": "paycheck", "edit_tx_open_rx_state_": false, "edit_tx_reconciled_rx_state_": false, "edit_tx_saving_rx_state_": false, "edit_tx_to_account_rx_state_": "", "edit_tx_type_rx_state_": "out", "editing_bid_rx_state_": "", "editing_budget_bid_rx_state_": "", "expanded_bucket_id_rx_state_": "", "expanded_bucket_txs_rx_state_": [], "expense_buckets_rx_state_": [], "fc_active_scenario_id_rx_state_": "", "fc_active_scenario_name_rx_state_": "", "fc_open_pids_rx_state_": [], "fc_safe_to_spend_rx_state_": "—", "fc_shortfall_count_rx_state_": 0, "fc_start_bal_rx_state_": "—", "fc_sts_color_rx_state_": "#818cf8", "fc_total_income_rx_state_": "—", "fc_total_unfunded_rx_state_": "—", "forecast_account_rx_state_": "", "forecast_accounts_rx_state_": [], "forecast_loading_rx_state_": false, "forecast_periods_rx_state_": [], "forecast_range_rx_state_": 3, "forecast_shortfall_label_rx_state_": "⚠ 0 periods with negative balance", "income_fmt_rx_state_": "$0.00", "income_total_rx_state_": 0.0, "insights_tab_rx_state_": "forecast", "is_loading_rx_state_": false, "is_logged_in_rx_state_": false, "last_month_income_rx_state_": 0.0, "last_month_income_fmt_rx_state_": "$0.00", "last_month_spent_rx_state_": 0.0, "last_month_spent_fmt_rx_state_": "$0.00", "ledger_acct_filter_rx_state_": "", "ledger_bucket_spend_rx_state_": [], "ledger_query_rx_state_": "", "ledger_rows_rx_state_": [], "ledger_tx_count_rx_state_": 0, "ledger_view_rx_state_": {"blocks": [], "income_fmt": "$0.00", "scheduled_fmt": "$0.00", "spent_fmt": "$0.00", "transferred_fmt": "$0.00", "has_scheduled": "", "empty": "1"}, "mom_better_rx_state_": false, "mom_verdict_rx_state_": "", "month_display_rx_state_": "", "month_is_closed_rx_state_": false, "month_status_str_rx_state_": "present", "next_mid_rx_state_": "", "panel_error_rx_state_": "", "paycheck_rows_rx_state_": [], "payday_amount_fmt_rx_state_": "", "payday_open_rx_state_": false, "payday_rows_rx_state_": [], "payday_saving_rx_state_": false, "payee_options_rx_state_": [], "payee_spend_rows_rx_state_": [], "prev_mid_rx_state_": "", "recon_account_id_rx_state_": "", "recon_account_name_rx_state_": "", "recon_can_finish_rx_state_": false, "recon_cleared_balance_rx_state_": 0.0, "recon_cleared_fmt_rx_state_": "$0.00", "recon_difference_rx_state_": 0.0, "recon_difference_fmt_rx_state_": "$0.00", "recon_error_rx_state_": "", "recon_open_rx_state_": false, "recon_saving_rx_state_": false, "recon_statement_balance_rx_state_": "", "recon_txs_rx_state_": [], "recon_unchecked_ids_rx_state_": [], "reports_tab_rx_state_": "snapshot", "rts_rx_state_": 0.0, "rts_color_rx_state_": "#30D158", "rts_fmt_rx_state_": "$0.00", "rts_negative_rx_state_": false, "rts_sub_rx_state_": "Every dollar has a job", "rts_zero_rx_state_": true, "rule_sheet_bid_rx_state_": "", "rule_sheet_error_rx_state_": "", "rule_sheet_itype_rx_state_": "internal", "rule_sheet_name_rx_state_": "", "rule_sheet_open_rx_state_": false, "rule_sheet_saving_rx_state_": false, "rule_sheet_val_type_rx_state_": "fixed", "rule_sheet_value_rx_state_": "", "setup_pc_amount_rx_state_": "", "setup_pc_anchor_rx_state_": "", "setup_pc_error_rx_state_": "", "setup_pc_freq_rx_state_": "14", "setup_pc_label_rx_state_": "", "setup_pc_saving_rx_state_": false, "sheet_account_rx_state_": "", "sheet_amount_rx_state_": "", "sheet_bucket_rx_state_": "", "sheet_date_rx_state_": "", "sheet_desc_rx_state_": "", "sheet_error_rx_state_": "", "sheet_income_type_rx_state_": "paycheck", "sheet_open_rx_state_": false, "sheet_saving_rx_state_": false, "sheet_to_account_rx_state_": "", "sheet_type_rx_state_": "out", "show_archived_cats_rx_state_": false, "spent_fmt_rx_state_": "$0.00", "spent_total_rx_state_": 0.0, "summary_cards_rx_state_": [], "tl_rows_rx_state_": [], "total_alloc_val_rx_state_": 0.0, "total_cash_rx_state_": 0.0, "total_cash_fmt_rx_state_": "$0.00", "total_debt_rx_state_": 0.0, "total_debt_fmt_rx_state_": "$0.00", "trend_rows_rx_state_": [], "trend_svg_rx_state_": "", "user_email_rx_state_": "", "user_id_rx_state_": "", "wi_active_rx_state_": false, "wi_active_pd_rx_state_": -1, "wi_active_scenario_id_rx_state_": "", "wi_balance_svg_rx_state_": "", "wi_bucket_overrides_rx_state_": {}, "wi_bucket_rows_rx_state_": [], "wi_chart_open_rx_state_": true, "wi_chart_svg_rx_state_": "", "wi_due_day_overrides_rx_state_": {}, "wi_grid_months_rx_state_": [{"mkey": "2026-6", "label": "Jun '26", "year": "2026", "month": "6"}, {"mkey": "2026-7", "label": "Jul '26", "year": "2026", "month": "7"}, {"mkey": "2026-8", "label": "Aug '26", "year": "2026", "month": "8"}, {"mkey": "2026-9", "label": "Sep '26", "year": "2026", "month": "9"}, {"mkey": "2026-10", "label": "Oct '26", "year": "2026", "month": "10"}, {"mkey": "2026-11", "label": "Nov '26", "year": "2026", "month": "11"}], "wi_grid_open_rx_state_": true, "wi_grid_rows_rx_state_": [], "wi_income_str_rx_state_": "", "wi_life_events_rx_state_": [], "wi_off_buckets_rx_state_": [], "wi_panel_open_rx_state_": {"chart": true, "grid": true, "periods": true}, "wi_periods_rx_state_": [], "wi_periods_open_rx_state_": true, "wi_pop_amount_rx_state_": "", "wi_pop_apply_from_rx_state_": "", "wi_pop_bkt_id_rx_state_": "", "wi_pop_enabled_rx_state_": true, "wi_pop_mkey_rx_state_": "", "wi_pop_open_rx_state_": false, "wi_pop_rules_rx_state_": [], "wi_rp_tab_rx_state_": "periods", "wi_rule_overrides_rx_state_": {}, "wi_rules_rows_rx_state_": [], "wi_safe_to_spend_rx_state_": "—", "wi_scenario_name_rx_state_": "", "wi_scenarios_rx_state_": [], "wi_scenarios_rls_error_rx_state_": false, "wi_schedule_rx_state_": {}, "wi_shortfall_count_rx_state_": 0, "wi_start_bal_rx_state_": "—", "wi_sts_color_rx_state_": "#818cf8", "wi_timeline_rx_state_": {}, "wi_total_income_rx_state_": "—", "wi_total_unfunded_rx_state_": "—"}, "reflex___state____state.reflex___istate___shared____shared_state_base_internal": {}, "reflex___state____state.reflex___state____frontend_event_exception_state": {}, "reflex___state____state.reflex___state____on_load_internal_state": {}, "reflex___state____state.reflex___state____update_vars_internal_state": {}}

export const defaultColorMode = "dark"
export const ColorModeContext = createContext({
  colorMode: defaultColorMode,
  resolvedColorMode: defaultColorMode === "dark" ? "dark" : "light",
  toggleColorMode: () => {},
  setColorMode: () => {},
});
export const UploadFilesContext = createContext(null);
export const DispatchContext = createContext(null);
export const StateContexts = {reflex___state____state: createContext(null),reflex___state____state__cura___state____app_state: createContext(null),reflex___state____state__reflex___istate___shared____shared_state_base_internal: createContext(null),reflex___state____state__reflex___state____frontend_event_exception_state: createContext(null),reflex___state____state__reflex___state____on_load_internal_state: createContext(null),reflex___state____state__reflex___state____update_vars_internal_state: createContext(null),};
export const EventLoopContext = createContext(null);
export const clientStorage = {"cookies": {"reflex___state____state.cura___state____app_state.access_token_rx_state_": {"name": "cura_at", "path": "/", "maxAge": 604800, "secure": true, "sameSite": "strict"}, "reflex___state____state.cura___state____app_state.user_id_rx_state_": {"name": "cura_uid", "path": "/", "maxAge": 604800, "secure": true, "sameSite": "strict"}}, "local_storage": {}, "session_storage": {}}


export const state_name = "reflex___state____state"

export const exception_state_name = "reflex___state____state.reflex___state____frontend_event_exception_state"

// These events are triggered on initial load and each page navigation.
export const onLoadInternalEvent = () => {
    const internal_events = [];

    // Get tracked cookie and local storage vars to send to the backend.
    const client_storage_vars = hydrateClientStorage(clientStorage);
    // But only send the vars if any are actually set in the browser.
    if (client_storage_vars && Object.keys(client_storage_vars).length !== 0) {
        internal_events.push(
            ReflexEvent(
                'reflex___state____state.reflex___state____update_vars_internal_state.update_vars_internal',
                {vars: client_storage_vars},
            ),
        );
    }

    // `on_load_internal` triggers the correct on_load event(s) for the current page.
    // If the page does not define any on_load event, this will just set `is_hydrated = true`.
    internal_events.push(ReflexEvent('reflex___state____state.reflex___state____on_load_internal_state.on_load_internal'));

    return internal_events;
}

// The following events are sent when the websocket connects or reconnects.
export const initialEvents = () => [
    ReflexEvent('reflex___state____state.hydrate'),
    ...onLoadInternalEvent()
]
    

export const isDevMode = true;

export function UploadFilesProvider({ children }) {
  const [filesById, setFilesById] = useState({})
  refs["__clear_selected_files"] = (id) => setFilesById(filesById => {
    const newFilesById = {...filesById}
    delete newFilesById[id]
    return newFilesById
  })
  return createElement(
    UploadFilesContext.Provider,
    { value: [filesById, setFilesById] },
    children
  );
}

export function ClientSide(component) {
  return ({ children, ...props }) => {
    const [Component, setComponent] = useState(null);
    useEffect(() => {
      async function load() {
        const comp = await component();
        setComponent(() => comp);
      }
      load();
    }, []);
    return Component ? jsx(Component, props, children) : null;
  };
}

export function EventLoopProvider({ children }) {
  const dispatch = useContext(DispatchContext)
  const [addEvents, connectErrors] = useEventLoop(
    dispatch,
    initialEvents,
    clientStorage,
  )
  return createElement(
    EventLoopContext.Provider,
    { value: [addEvents, connectErrors] },
    children
  );
}

export function StateProvider({ children }) {
  const [reflex___state____state, dispatch_reflex___state____state] = useReducer(applyDelta, initialState["reflex___state____state"])
const [reflex___state____state__cura___state____app_state, dispatch_reflex___state____state__cura___state____app_state] = useReducer(applyDelta, initialState["reflex___state____state.cura___state____app_state"])
const [reflex___state____state__reflex___istate___shared____shared_state_base_internal, dispatch_reflex___state____state__reflex___istate___shared____shared_state_base_internal] = useReducer(applyDelta, initialState["reflex___state____state.reflex___istate___shared____shared_state_base_internal"])
const [reflex___state____state__reflex___state____frontend_event_exception_state, dispatch_reflex___state____state__reflex___state____frontend_event_exception_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____frontend_event_exception_state"])
const [reflex___state____state__reflex___state____on_load_internal_state, dispatch_reflex___state____state__reflex___state____on_load_internal_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____on_load_internal_state"])
const [reflex___state____state__reflex___state____update_vars_internal_state, dispatch_reflex___state____state__reflex___state____update_vars_internal_state] = useReducer(applyDelta, initialState["reflex___state____state.reflex___state____update_vars_internal_state"])
  const dispatchers = useMemo(() => {
    return {
      "reflex___state____state": dispatch_reflex___state____state,
"reflex___state____state.cura___state____app_state": dispatch_reflex___state____state__cura___state____app_state,
"reflex___state____state.reflex___istate___shared____shared_state_base_internal": dispatch_reflex___state____state__reflex___istate___shared____shared_state_base_internal,
"reflex___state____state.reflex___state____frontend_event_exception_state": dispatch_reflex___state____state__reflex___state____frontend_event_exception_state,
"reflex___state____state.reflex___state____on_load_internal_state": dispatch_reflex___state____state__reflex___state____on_load_internal_state,
"reflex___state____state.reflex___state____update_vars_internal_state": dispatch_reflex___state____state__reflex___state____update_vars_internal_state,
    }
  }, [])

  return (
    createElement(StateContexts.reflex___state____state,{value: reflex___state____state},
createElement(StateContexts.reflex___state____state__cura___state____app_state,{value: reflex___state____state__cura___state____app_state},
createElement(StateContexts.reflex___state____state__reflex___istate___shared____shared_state_base_internal,{value: reflex___state____state__reflex___istate___shared____shared_state_base_internal},
createElement(StateContexts.reflex___state____state__reflex___state____frontend_event_exception_state,{value: reflex___state____state__reflex___state____frontend_event_exception_state},
createElement(StateContexts.reflex___state____state__reflex___state____on_load_internal_state,{value: reflex___state____state__reflex___state____on_load_internal_state},
createElement(StateContexts.reflex___state____state__reflex___state____update_vars_internal_state,{value: reflex___state____state__reflex___state____update_vars_internal_state},
    createElement(DispatchContext, {value: dispatchers}, children)
    ))))))
  )
}