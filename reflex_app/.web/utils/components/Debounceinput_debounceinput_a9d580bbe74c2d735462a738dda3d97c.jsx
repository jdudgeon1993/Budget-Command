
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextArea as RadixThemesTextArea} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_a9d580bbe74c2d735462a738dda3d97c = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_7d5130ce10f1a1b5c0b79e2e35d7971f = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_notes", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontFamily"] : "Rajdhani, system-ui, sans-serif", ["--default-font-family"] : "Rajdhani, system-ui, sans-serif", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }), ["resize"] : "none" }),debounceTimeout:300,element:RadixThemesTextArea,onChange:on_change_7d5130ce10f1a1b5c0b79e2e35d7971f,placeholder:"Optional notes\u2026",rows:"2",value:reflex___state____state__cura___state____app_state.bsf_notes_rx_state_},)
    )
});
