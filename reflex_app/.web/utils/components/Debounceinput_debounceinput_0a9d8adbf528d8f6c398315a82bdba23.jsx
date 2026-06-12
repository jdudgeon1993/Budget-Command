
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_0a9d8adbf528d8f6c398315a82bdba23 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_7ec9a8c26223767cfd534a0835ba6770 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_rule_sheet_name", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["padding"] : "8px 12px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#818cf8" }), ["&:placeholder"] : ({ ["color"] : "#4e4e6a" }), ["width"] : "100%" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_7ec9a8c26223767cfd534a0835ba6770,placeholder:"e.g. 5% to Emergency Fund",type:"text",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.rule_sheet_name_rx_state_) ? reflex___state____state__cura___state____app_state.rule_sheet_name_rx_state_ : "")},)
    )
});
