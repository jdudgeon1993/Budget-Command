
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isNotNullOrUndefined,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Input_input_450b6cd9eab127844cc4abd451f0d79f = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_8d5cc514c201791af709edab3c9e6bec = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_add_acct_color", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("input",{css:({ ["width"] : "100%", ["height"] : "36px", ["borderRadius"] : "8px", ["border"] : "1px solid #252535", ["cursor"] : "pointer", ["background"] : "transparent", ["padding"] : "2px" }),onChange:on_change_8d5cc514c201791af709edab3c9e6bec,type:"color",value:(isNotNullOrUndefined(reflex___state____state__cura___state____app_state.add_acct_color_rx_state_) ? reflex___state____state__cura___state____app_state.add_acct_color_rx_state_ : "")},)
    )
});
