
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_b4b4c11469d2d6ff21782a956e6fe464 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_7430c26bc725f8fd3265b16f450ec870 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_due_amount", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,inputMode:"decimal",onChange:on_change_7430c26bc725f8fd3265b16f450ec870,placeholder:"exact $ due",type:"number",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.bsf_due_amount_rx_state_) ? reflex___state____state__cura___state____app_state.bsf_due_amount_rx_state_ : "")},)
    )
});
