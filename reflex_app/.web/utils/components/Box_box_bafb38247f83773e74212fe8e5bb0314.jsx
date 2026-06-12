
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_bafb38247f83773e74212fe8e5bb0314 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_639b1981bc47edf1e1997ed3d03ce750 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.reset_whatif", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#606088", ["cursor"] : "pointer", ["padding"] : "3px 8px", ["borderRadius"] : "5px", ["border"] : "1px solid rgba(255,255,255,0.08)", ["&:hover"] : ({ ["color"] : "#FF453A", ["borderColor"] : "#FF453A44" }) }),onClick:on_click_639b1981bc47edf1e1997ed3d03ce750,role:"button",tabIndex:0},children)
    )
});
