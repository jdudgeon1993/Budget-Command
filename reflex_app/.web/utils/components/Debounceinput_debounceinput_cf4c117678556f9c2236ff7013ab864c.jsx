
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_cf4c117678556f9c2236ff7013ab864c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_6fa22796a0702c340bde052d5ffa0270 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_setup_pc_label", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "12px", ["padding"] : "8px 12px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["flex"] : "2" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_6fa22796a0702c340bde052d5ffa0270,placeholder:"Label (e.g. Main Job)",type:"text",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.setup_pc_label_rx_state_) ? reflex___state____state__cura___state____app_state.setup_pc_label_rx_state_ : "")},)
    )
});
