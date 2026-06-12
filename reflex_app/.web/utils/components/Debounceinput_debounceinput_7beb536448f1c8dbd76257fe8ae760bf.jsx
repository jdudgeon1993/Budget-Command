
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import DebounceInput from "react-debounce-input"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {TextField as RadixThemesTextField} from "@radix-ui/themes"
import {jsx} from "@emotion/react"






export const Debounceinput_debounceinput_7beb536448f1c8dbd76257fe8ae760bf = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_228f6730eccb25a2f528894cff4dd8b2 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_ledger_query", ({ ["q"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx(DebounceInput,{css:({ ["background"] : "transparent", ["border"] : "none", ["outline"] : "none", ["color"] : "#f0f0fa", ["fontFamily"] : "'Share Tech Mono', monospace", ["--default-font-family"] : "'Share Tech Mono', monospace", ["fontSize"] : "12px", ["flex"] : "1", ["width"] : "100%" }),debounceTimeout:300,element:RadixThemesTextField.Root,onChange:on_change_228f6730eccb25a2f528894cff4dd8b2,placeholder:"Search transactions\u2026",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.ledger_query_rx_state_) ? reflex___state____state__cura___state____app_state.ledger_query_rx_state_ : "")},)
    )
});
