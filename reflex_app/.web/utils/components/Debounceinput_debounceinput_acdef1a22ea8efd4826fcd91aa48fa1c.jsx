
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_acdef1a22ea8efd4826fcd91aa48fa1c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_29bd9ce2fad25bd0d7201cd1bc671692 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_amount", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "in"?.valueOf?.()) ? "#30D158" : ((reflex___state____state__cura___state____app_state.edit_tx_type_rx_state_?.valueOf?.() === "out"?.valueOf?.()) ? "#FF453A" : "#9090B8")), ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2", ["outline"] : "none" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["textAlign"] : "center" }),debounceTimeout:300,element:RadixThemesTextField.Root,inputMode:"decimal",onChange:on_change_29bd9ce2fad25bd0d7201cd1bc671692,type:"number",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.edit_tx_amount_rx_state_) ? reflex___state____state__cura___state____app_state.edit_tx_amount_rx_state_ : "")},)
    )
});
