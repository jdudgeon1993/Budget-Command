
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_66ef4d08bd0048bd91de8022888c938b = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_497381a435c61a3f40c7b60046c9db69 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.clear_fc_scenario", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "12px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "2px 8px", ["borderRadius"] : "6px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["&:hover"] : ({ ["color"] : "#FF453A", ["borderColor"] : "#FF453A44" }) }),onClick:on_click_497381a435c61a3f40c7b60046c9db69},children)
    )
});
