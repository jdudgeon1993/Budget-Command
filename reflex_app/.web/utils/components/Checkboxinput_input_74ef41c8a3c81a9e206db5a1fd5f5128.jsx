
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Checkboxinput_input_74ef41c8a3c81a9e206db5a1fd5f5128 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_c347928aab416928f1f8b52fd915691e = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_acct_settings_is_promo", ({ ["value"] : _e?.["target"]?.["checked"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("input",{checked:reflex___state____state__cura___state____app_state.acct_settings_is_promo_rx_state_,css:({ ["cursor"] : "pointer", ["width"] : "16px", ["height"] : "16px" }),onChange:on_change_c347928aab416928f1f8b52fd915691e,type:"checkbox"},)
    )
});
