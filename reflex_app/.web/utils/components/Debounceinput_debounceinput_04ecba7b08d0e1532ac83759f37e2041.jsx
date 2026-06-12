
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_04ecba7b08d0e1532ac83759f37e2041 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_5222d8bcc1579c72bf0b6e1c5ff26658 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_bkt_name", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["outline"] : "none", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2" }), ["&:placeholder"] : ({ ["color"] : "#606088" }), ["flex"] : "1", ["minWidth"] : "0" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_5222d8bcc1579c72bf0b6e1c5ff26658,placeholder:"Bucket name\u2026",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.add_bkt_name_rx_state_) ? reflex___state____state__cura___state____app_state.add_bkt_name_rx_state_ : "")},)
    )
});
