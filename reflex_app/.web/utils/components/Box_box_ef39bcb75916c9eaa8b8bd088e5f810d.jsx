
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_ef39bcb75916c9eaa8b8bd088e5f810d = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a5fd45cc004314db8ee0f75ba879ae32 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.logout", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Sign out",css:({ ["fontSize"] : "14px", ["color"] : "rgba(255,255,255,0.22)", ["cursor"] : "pointer", ["padding"] : "4px 6px", ["borderRadius"] : "4px", ["&:hover"] : ({ ["color"] : "rgba(255,255,255,0.55)" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #BF5AF2", ["outlineOffset"] : "2px" }) }),onClick:on_click_a5fd45cc004314db8ee0f75ba879ae32,role:"button",tabIndex:0},children)
    )
});
