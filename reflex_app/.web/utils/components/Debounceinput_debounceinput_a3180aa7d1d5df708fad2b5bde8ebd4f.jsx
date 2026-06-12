
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_a3180aa7d1d5df708fad2b5bde8ebd4f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_b5c03592bfaaefb7acc33cbb67689f30 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_setup_pc_anchor", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["padding"] : "8px 12px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#818cf8" }), ["&:placeholder"] : ({ ["color"] : "#6868a2" }), ["flex"] : "2" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_b5c03592bfaaefb7acc33cbb67689f30,placeholder:"Anchor date (YYYY-MM-DD)",type:"text",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.setup_pc_anchor_rx_state_) ? reflex___state____state__cura___state____app_state.setup_pc_anchor_rx_state_ : "")},)
    )
});
