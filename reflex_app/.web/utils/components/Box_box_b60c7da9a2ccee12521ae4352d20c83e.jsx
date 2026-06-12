
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_b60c7da9a2ccee12521ae4352d20c83e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_639b1981bc47edf1e1997ed3d03ce750 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.reset_whatif", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["fontSize"] : "11px", ["color"] : "#f87171", ["cursor"] : "pointer", ["padding"] : "3px 8px", ["borderRadius"] : "6px", ["border"] : "1px solid #f8717144", ["background"] : "#f8717112", ["&:hover"] : ({ ["background"] : "#f8717122" }) }),onClick:on_click_639b1981bc47edf1e1997ed3d03ce750},children)
    )
});
