
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_8fbc4cd18760898dec1f8237d6ca2264 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_7bfb5e1f99db3dce8310e5c39a1d25d4 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_recon_statement_balance", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{autoFocus:true,css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "22px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2", ["outline"] : "none" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["textAlign"] : "center", ["fontWeight"] : "700", ["borderColor"] : (!((reflex___state____state__cura___state____app_state.recon_statement_balance_rx_state_?.valueOf?.() === ""?.valueOf?.())) ? (reflex___state____state__cura___state____app_state.recon_can_finish_rx_state_ ? "#30D158" : "rgba(255,255,255,0.08)") : "rgba(255,255,255,0.08)") }),debounceTimeout:300,element:RadixThemesTextField.Root,inputMode:"decimal",onChange:on_change_7bfb5e1f99db3dce8310e5c39a1d25d4,placeholder:"0.00",type:"text",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.recon_statement_balance_rx_state_) ? reflex___state____state__cura___state____app_state.recon_statement_balance_rx_state_ : "")},)
    )
});
