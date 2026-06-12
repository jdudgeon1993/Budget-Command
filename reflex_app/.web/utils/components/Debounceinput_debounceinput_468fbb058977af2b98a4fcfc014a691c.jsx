
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_468fbb058977af2b98a4fcfc014a691c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_28b09e84e4c133c7a7d9728f6cec08ec = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_budget", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,inputMode:"decimal",onChange:on_change_28b09e84e4c133c7a7d9728f6cec08ec,placeholder:"0",type:"number",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.bsf_budget_rx_state_) ? reflex___state____state__cura___state____app_state.bsf_budget_rx_state_ : "")},)
    )
});
