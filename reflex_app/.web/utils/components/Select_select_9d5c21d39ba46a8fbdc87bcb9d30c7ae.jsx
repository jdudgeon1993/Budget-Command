
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_9d5c21d39ba46a8fbdc87bcb9d30c7ae = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_2d52707f42a30a7090186e468bd3d1b2 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_recon_account_id", ({ ["v"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["width"] : "100%", ["marginBottom"] : "4px" }),onChange:on_change_2d52707f42a30a7090186e468bd3d1b2,value:reflex___state____state__cura___state____app_state.recon_account_id_rx_state_},children)
    )
});
