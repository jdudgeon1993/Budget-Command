
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_b1340c6733a804477de1781643121b6e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_a763f34a3b3fa0c245e2749c6cddc830 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_pop_amount", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["padding"] : "10px 12px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "14px", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2", ["outline"] : "none", ["boxShadow"] : "0 0 0 3px #BF5AF222" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_a763f34a3b3fa0c245e2749c6cddc830,placeholder:"e.g. 1800",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.wi_pop_amount_rx_state_) ? reflex___state____state__cura___state____app_state.wi_pop_amount_rx_state_ : "")},)
    )
});
