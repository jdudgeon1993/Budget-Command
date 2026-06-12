
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {EventLoopContext,StateContexts} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Select_select_1822da147c4b98efe94aba3de8ef96d0 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_change_639904d08ae8c4f47c9652a9df11c439 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.set_sheet_income_type", ({ ["value"] : _e?.["target"]?.["value"] }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])
const reflex___state____state__cura___state____app_state = useContext(StateContexts.reflex___state____state__cura___state____app_state)



    return(
        jsx("select",{css:({ ["background"] : "#1c1c25", ["border"] : "1px solid #252535", ["borderRadius"] : "8px", ["color"] : "#f0f0fa", ["fontSize"] : "13px", ["padding"] : "8px 10px", ["width"] : "100%" }),onChange:on_change_639904d08ae8c4f47c9652a9df11c439,value:reflex___state____state__cura___state____app_state.sheet_income_type_rx_state_},children)
    )
});
