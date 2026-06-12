
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_857d89d0d2976773bfe5554ed76c9a7a = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_6d40a3b40f950a477a6b13f5b0d2f71e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_desc", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_6d40a3b40f950a477a6b13f5b0d2f71e,placeholder:"Description",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.sheet_desc_rx_state_) ? reflex___state____state__cura___state____app_state.sheet_desc_rx_state_ : "")},)
    )
});
