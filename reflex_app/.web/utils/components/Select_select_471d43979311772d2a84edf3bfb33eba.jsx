
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_471d43979311772d2a84edf3bfb33eba = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_4d8262fe432ef638a2d08f5362846ab0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_edit_tx_income_type", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["width"] : "100%" }),onChange:on_change_4d8262fe432ef638a2d08f5362846ab0,value:reflex___state____state__cura___state____app_state.edit_tx_income_type_rx_state_},children)
    )
});
