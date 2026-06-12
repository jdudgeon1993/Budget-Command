
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_5d6c6aac9596b22b8ed179843ccfe5f4 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_a5fd45cc004314db8ee0f75ba879ae32 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.logout", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{"aria-label":"Sign out",css:({ ["fontSize"] : "12px", ["color"] : "#6868a2", ["cursor"] : "pointer", ["padding"] : "4px 8px", ["borderRadius"] : "4px", ["&:hover"] : ({ ["color"] : "#8282a2" }), ["&:focus-visible"] : ({ ["outline"] : "2px solid #818cf8", ["outlineOffset"] : "2px" }) }),onClick:on_click_a5fd45cc004314db8ee0f75ba879ae32,role:"button",tabIndex:0},children)
    )
});
