
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_0bdcb29994d7b4fb2dfc92dbf7c448bc = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_9d328f11c9d51d77ef0c61dfc676e50c = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_acct_settings_min_pay", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2", ["outline"] : "none" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["inputMode"] : "decimal" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_9d328f11c9d51d77ef0c61dfc676e50c,placeholder:"e.g. 25.00",type:"number",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.acct_settings_min_pay_rx_state_) ? reflex___state____state__cura___state____app_state.acct_settings_min_pay_rx_state_ : "")},)
    )
});
