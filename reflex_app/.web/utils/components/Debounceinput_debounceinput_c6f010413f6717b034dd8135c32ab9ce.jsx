
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_c6f010413f6717b034dd8135c32ab9ce = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_16af3fc68d220c2f0cdf1bf1e6118eef = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_debt_pay_amount", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }), ["&:placeholder"] : ({ ["color"] : "#6868a2" }), ["inputMode"] : "decimal" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_16af3fc68d220c2f0cdf1bf1e6118eef,placeholder:"0.00",type:"number",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.debt_pay_amount_rx_state_) ? reflex___state____state__cura___state____app_state.debt_pay_amount_rx_state_ : "")},)
    )
});
