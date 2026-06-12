
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_cf50b3144e09e339fc4561a60462307d = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_a9b8f430e357b79aa58e1615fa9afaab = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_date", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["fontSize"] : "13px", ["padding"] : "8px 12px", ["outline"] : "none", ["width"] : "100%", ["&:focus"] : ({ ["borderColor"] : "#BF5AF2", ["outline"] : "none" }), ["&:placeholder"] : ({ ["color"] : "#606088" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_a9b8f430e357b79aa58e1615fa9afaab,type:"date",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.sheet_date_rx_state_) ? reflex___state____state__cura___state____app_state.sheet_date_rx_state_ : "")},)
    )
});
