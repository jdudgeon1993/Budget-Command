
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_0189bdbaa1eb2d9f33f7f594766ed7fb = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_638f003af976017edb59d94223eb8e30 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_bsf_cat_id", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "rgba(255,255,255,0.08)", ["border"] : "1px solid rgba(255,255,255,0.08)", ["borderRadius"] : "8px", ["color"] : "#FFFFFF", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["width"] : "100%" }),onChange:on_change_638f003af976017edb59d94223eb8e30,value:reflex___state____state__cura___state____app_state.bsf_cat_id_rx_state_},children)
    )
});
