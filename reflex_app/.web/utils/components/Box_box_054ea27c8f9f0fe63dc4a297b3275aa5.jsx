
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_054ea27c8f9f0fe63dc4a297b3275aa5 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_d04331f39bea52a415abbd0f96bef6b0 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.go_next_month", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Next month",css:({ ["cursor"] : "pointer", ["color"] : "#6868a2", ["padding"] : "6px 10px", ["borderRadius"] : "6px", ["fontSize"] : "15px", ["&:hover"] : ({ ["color"] : "#818cf8", ["background"] : "#1c1c25" }) }),onClick:on_click_d04331f39bea52a415abbd0f96bef6b0,role:"button",tabIndex:0},children)
    )
});
