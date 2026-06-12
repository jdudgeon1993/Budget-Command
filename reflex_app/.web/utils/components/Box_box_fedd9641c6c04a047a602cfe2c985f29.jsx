
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_fedd9641c6c04a047a602cfe2c985f29 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_497381a435c61a3f40c7b60046c9db69 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.clear_fc_scenario", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["padding"] : "2px 8px", ["borderRadius"] : "6px", ["border"] : "1px solid #252535", ["&:hover"] : ({ ["color"] : "#f87171", ["borderColor"] : "#f8717144" }) }),onClick:on_click_497381a435c61a3f40c7b60046c9db69},children)
    )
});
