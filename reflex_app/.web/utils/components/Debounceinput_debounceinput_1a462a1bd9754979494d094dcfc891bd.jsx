
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_1a462a1bd9754979494d094dcfc891bd = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_1389b9c9af0f5f7c88bf412e7c35f4bb = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_wi_income", ({ ["val"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["padding"] : "8px 12px", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "13px", ["width"] : "200px", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_1389b9c9af0f5f7c88bf412e7c35f4bb,placeholder:"Monthly income (e.g. 5000)",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.wi_income_str_rx_state_) ? reflex___state____state__cura___state____app_state.wi_income_str_rx_state_ : "")},)
    )
});
