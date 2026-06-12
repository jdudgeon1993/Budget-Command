
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_a7e1f21eacefb5c9bea9283d9a158e76 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_266fc2082b4174a2f61335c528a1e5c1 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_wi_scenario_name", ({ ["val"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["padding"] : "6px 12px", ["color"] : "#f0f0fa", ["fontSize"] : "12px", ["flex"] : "1", ["&:focus"] : ({ ["borderColor"] : "#818cf8", ["outline"] : "none" }) }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_266fc2082b4174a2f61335c528a1e5c1,placeholder:"Name this scenario\u2026",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.wi_scenario_name_rx_state_) ? reflex___state____state__cura___state____app_state.wi_scenario_name_rx_state_ : "")},)
    )
});
